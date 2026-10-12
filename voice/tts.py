import logging
import platform
import shutil
import subprocess
import sys
import threading
from pathlib import Path
import numpy as np
import sounddevice as sd


def _resolve_runtime_file(relative_path):
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        project_root / relative_path,
        Path(sys.executable).resolve().parent / relative_path,
    ]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return project_root / relative_path


MODEL = _resolve_runtime_file(Path("voice") / "models" / "en_US-lessac-medium.onnx")
OUTPUT = _resolve_runtime_file(Path("voice") / "tts_output.wav")
TARGET_PEAK = 0.84
FADE_SECONDS = 0.012

_VOICE_INSTANCE = None
_VOICE_LOCK = threading.Lock()
_IS_PLAYING = threading.Event()
_PLAYBACK_LOCK = threading.Lock()
_PLAYBACK_GENERATION = 0
player = None


def get_piper_voice():
    """Returns a cached, in-memory PiperVoice instance for sub-100ms TTS synthesis."""
    global _VOICE_INSTANCE
    if _VOICE_INSTANCE is None:
        with _VOICE_LOCK:
            if _VOICE_INSTANCE is None:
                try:
                    from piper import PiperVoice
                    logging.info(f"Loading in-memory PiperVoice from {MODEL}...")
                    _VOICE_INSTANCE = PiperVoice.load(str(MODEL))
                    logging.info("PiperVoice loaded in-memory successfully.")
                except Exception as exc:
                    logging.error(f"Failed to load PiperVoice in-memory: {exc}")
                    _VOICE_INSTANCE = None
    return _VOICE_INSTANCE


def preload_tts():
    """Preloads the Piper voice model into RAM during assistant startup."""
    threading.Thread(target=get_piper_voice, name="tts-preload-thread", daemon=True).start()


def speak(text, block=False):
    """
    Synthesizes polished speech and plays it with stable volume and clean edges.
    """
    if not text or not text.strip():
        return

    text = _prepare_speech_text(text)
    if not text:
        return

    # Stop any current speech
    stop_speaking()

    voice = get_piper_voice()
    if voice is not None:
        try:
            chunks = list(voice.synthesize(text.strip()))
            if not chunks:
                return

            audio_arrays = [c.audio_float_array for c in chunks if hasattr(c, "audio_float_array")]
            if audio_arrays:
                audio = _finish_audio(np.concatenate(audio_arrays), voice.config.sample_rate)
                sample_rate = voice.config.sample_rate

                _start_sounddevice_playback(audio, sample_rate, block)
                return
        except Exception as exc:
            logging.error(f"In-memory Piper synthesis failed, falling back to subprocess: {exc}")

    # Fallback to subprocess mode if in-memory fails
    _speak_fallback(text)


def _speak_fallback(text):
    global player
    try:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "-m",
            "piper",
            "-m",
            str(MODEL),
            "-f",
            str(OUTPUT),
        ]
        subprocess.run(command, input=text, text=True, check=True)

        if platform.system() == "Windows":
            # winsound is part of Windows Python and avoids a PowerShell
            # dependency in both development and packaged installations.
            import winsound

            global _PLAYBACK_GENERATION
            with _PLAYBACK_LOCK:
                _PLAYBACK_GENERATION += 1
                generation = _PLAYBACK_GENERATION
                _IS_PLAYING.set()

            def play_wav():
                try:
                    winsound.PlaySound(str(OUTPUT), winsound.SND_FILENAME)
                finally:
                    with _PLAYBACK_LOCK:
                        if generation == _PLAYBACK_GENERATION:
                            _IS_PLAYING.clear()

            threading.Thread(target=play_wav, name="winsound-playback", daemon=True).start()
            return
        else:
            playback_command = _fallback_playback_command()
            popen_options = {}

        process = subprocess.Popen(playback_command, **popen_options)
        _start_process_playback(process)
    except Exception as exc:
        logging.error(f"Fallback TTS failed: {exc}")


def _prepare_speech_text(text):
    """Remove visual formatting that sounds unnatural when spoken aloud."""
    import re

    clean = str(text).strip()
    clean = re.sub(r"```.*?```", "", clean, flags=re.DOTALL)
    clean = re.sub(r"[*_#>`]", "", clean)
    clean = re.sub(r"^\s*[-•]\s+", "", clean, flags=re.MULTILINE)
    clean = clean.replace("&", " and ")
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _finish_audio(audio, sample_rate):
    """Apply gentle mastering so speech starts and ends smoothly."""
    audio = np.asarray(audio, dtype=np.float32)
    if audio.size == 0:
        return audio

    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio = audio * min(1.0, TARGET_PEAK / peak)

    fade_samples = min(int(sample_rate * FADE_SECONDS), audio.size // 2)
    if fade_samples > 0:
        audio[:fade_samples] *= np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
        audio[-fade_samples:] *= np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
    return np.clip(audio, -1.0, 1.0)


def _fallback_playback_command():
    players = {
        "Linux": ("paplay", "aplay", "ffplay"),
        "Darwin": ("afplay",),
    }.get(platform.system(), ())
    for executable in players:
        player_path = shutil.which(executable)
        if player_path:
            if executable == "ffplay":
                return [
                    player_path,
                    "-nodisp",
                    "-autoexit",
                    "-loglevel",
                    "error",
                    str(OUTPUT),
                ]
            return [player_path, str(OUTPUT)]
    raise RuntimeError(
        f"No supported audio playback command was found for {platform.system()}."
    )


def _start_sounddevice_playback(audio, sample_rate, block):
    global _PLAYBACK_GENERATION
    with _PLAYBACK_LOCK:
        _PLAYBACK_GENERATION += 1
        generation = _PLAYBACK_GENERATION
        _IS_PLAYING.set()
        try:
            sd.play(audio, samplerate=sample_rate)
        except Exception:
            _IS_PLAYING.clear()
            raise

    if block:
        _wait_for_sounddevice_playback(generation)
    else:
        threading.Thread(
            target=_wait_for_sounddevice_playback,
            args=(generation,),
            name="tts-playback-monitor",
            daemon=True,
        ).start()


def _wait_for_sounddevice_playback(generation):
    try:
        sd.wait()
    except Exception:
        logging.exception("Waiting for speech playback failed.")
    finally:
        with _PLAYBACK_LOCK:
            if generation == _PLAYBACK_GENERATION:
                _IS_PLAYING.clear()


def _start_process_playback(process):
    global _PLAYBACK_GENERATION, player
    with _PLAYBACK_LOCK:
        _PLAYBACK_GENERATION += 1
        generation = _PLAYBACK_GENERATION
        player = process
        _IS_PLAYING.set()
    threading.Thread(
        target=_wait_for_process_playback,
        args=(process, generation),
        name="tts-process-monitor",
        daemon=True,
    ).start()


def _wait_for_process_playback(process, generation):
    global player
    try:
        process.wait()
    except Exception:
        logging.exception("Waiting for speech playback process failed.")
    finally:
        with _PLAYBACK_LOCK:
            if generation == _PLAYBACK_GENERATION:
                if player is process:
                    player = None
                _IS_PLAYING.clear()


def stop_speaking():
    """Stop active audio playback."""
    global _PLAYBACK_GENERATION, player
    with _PLAYBACK_LOCK:
        _PLAYBACK_GENERATION += 1
        active_player = player
        player = None
        _IS_PLAYING.clear()

    try:
        sd.stop()
    except Exception:
        logging.exception("Could not stop sounddevice playback.")

    if platform.system() == "Windows":
        try:
            import winsound

            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            logging.exception("Could not stop Windows audio playback.")

    if active_player is not None and active_player.poll() is None:
        active_player.terminate()
        try:
            active_player.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            active_player.kill()
            active_player.wait()


def is_speaking():
    """Checks whether speech audio is currently playing."""
    if player is not None and player.poll() is None:
        return True
    return _IS_PLAYING.is_set()


if __name__ == "__main__":
    import time
    print("Testing ultra-fast in-memory TTS...")
    t0 = time.perf_counter()
    speak("Yes?")
    print(f"Time to start speaking: {round((time.perf_counter() - t0)*1000, 1)}ms")
    time.sleep(1)
    stop_speaking()
    print("TTS test completed.")
