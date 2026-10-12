import signal
import sys
import threading
import time
import logging
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

log_directory = Path.home() / ".us-ai"
log_directory.mkdir(parents=True, exist_ok=True)
log_file = log_directory / "assistant.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
if sys.stdout is None:
    sys.stdout = log_file.open("a", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = sys.stdout

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
from silero_vad import VADIterator, load_silero_vad

from brain.brain import ask_ai
from brain.command_parser import parse_command
from brain.conversation import ConversationManager
from core.controller import execute
from core.web_search import (
    search_web,
    should_search_web_first,
    spoken_web_answer,
    web_search_failure_message,
)
from voice.tts import is_speaking, speak, stop_speaking, get_piper_voice
from voice.orb import AssistantOrb
from voice.tray_icon import AssistantTray
from config.settings import LOG_TRANSCRIPTS
from config.settings import ALLOW_BARGE_IN

SAMPLE_RATE = 16000
MIC_SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_SIZE = 512
MIC_CHUNK_SIZE = CHUNK_SIZE * (MIC_SAMPLE_RATE // SAMPLE_RATE)
END_OF_SPEECH_SILENCE_MS = 1000
VAD_THRESHOLD = 0.25
MAX_TRANSCRIPTION_GAIN = 12.0
TARGET_TRANSCRIPTION_PEAK = 0.2
MIC_DEVICE = None
_last_logged_mic_device = None
orb = None
_instance_mutex_handle = None
_kernel32 = None


class MicrophoneUnavailableError(RuntimeError):
    pass


def resolve_mic_device():
    """Prefer the default Windows WASAPI input, falling back to other devices."""
    try:
        devices = sd.query_devices()
        host_apis = sd.query_hostapis()
    except sd.PortAudioError as exc:
        raise MicrophoneUnavailableError(
            f"Could not enumerate audio devices: {exc}"
        ) from exc

    default_device = sd.default.device[0]
    candidate_indices = []
    # Follow the microphone selected by Windows first. Some USB headsets
    # expose separate MME/WASAPI endpoints with different capture levels.
    if isinstance(default_device, int) and default_device >= 0:
        candidate_indices.append(default_device)

    wasapi_index = next(
        (index for index, api in enumerate(host_apis) if api["name"] == "Windows WASAPI"),
        None,
    )
    if wasapi_index is not None:
        wasapi_default = host_apis[wasapi_index]["default_input_device"]
        if isinstance(wasapi_default, int) and wasapi_default >= 0:
            candidate_indices.append(wasapi_default)
    candidate_indices.extend(
        index
        for index, device in enumerate(devices)
        if device["max_input_channels"] > 0 and index not in candidate_indices
    )

    for device_index in candidate_indices:
        device = devices[device_index]
        if device["max_input_channels"] < CHANNELS:
            continue
        try:
            sd.check_input_settings(
                device=device_index,
                channels=CHANNELS,
                samplerate=MIC_SAMPLE_RATE,
                dtype="float32",
            )
        except sd.PortAudioError:
            continue

        global _last_logged_mic_device
        if device_index != _last_logged_mic_device:
            logging.info(
                "Using microphone input %s (%s): %s at %d Hz",
                device_index,
                host_apis[device["hostapi"]]["name"],
                device["name"],
                MIC_SAMPLE_RATE,
            )
            _last_logged_mic_device = device_index
        return device_index

    raise MicrophoneUnavailableError(
        "No available microphone supports mono audio at 16 kHz. "
        "Connect or enable a microphone in Windows Sound settings."
    )


print("Loading background assistant models...")

logging.info("Loading speech and TTS models.")
vad_model = load_silero_vad()
whisper = WhisperModel("base", device="cpu", compute_type="int8")
get_piper_voice()


def create_vad():
    return VADIterator(
        vad_model,
        threshold=VAD_THRESHOLD,
        sampling_rate=SAMPLE_RATE,
        min_silence_duration_ms=END_OF_SPEECH_SILENCE_MS,
        speech_pad_ms=200,
    )


def downsample_microphone_chunk(data):
    """Converts one 48 kHz mono microphone block into the VAD's 16 kHz block."""
    samples = np.asarray(data[:, 0], dtype=np.float32)
    return samples.reshape(CHUNK_SIZE, MIC_SAMPLE_RATE // SAMPLE_RATE).mean(axis=1)


def transcribe_audio(audio):
    if audio is None:
        return ""
    peak = float(np.max(np.abs(audio)))
    gain = (
        min(MAX_TRANSCRIPTION_GAIN, TARGET_TRANSCRIPTION_PEAK / peak)
        if 0 < peak < TARGET_TRANSCRIPTION_PEAK
        else 1.0
    )
    if gain > 1:
        logging.info("Boosting quiet speech by %.1fx before transcription.", gain)
    audio = np.clip(np.asarray(audio, dtype=np.float32) * gain, -1.0, 1.0)
    segments, _ = whisper.transcribe(
        audio,
        language="en",
        beam_size=1,
        temperature=0,
        vad_filter=False,
        condition_on_previous_text=False,
    )
    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )
    return text.strip()


def record_until_speech_end():
    vad = create_vad()
    chunks = []
    recent_chunks = deque(maxlen=6)
    speaking = False
    start_time = time.monotonic()

    with sd.InputStream(
        samplerate=MIC_SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=MIC_CHUNK_SIZE,
        device=resolve_mic_device(),
    ) as stream:
        while True:
            if orb is not None and orb.stopped:
                break
            if mic_muted:
                vad.reset_states()
                return None
            if time.monotonic() - start_time > 30:
                break

            data, overflowed = stream.read(MIC_CHUNK_SIZE)
            if overflowed:
                continue

            chunk = downsample_microphone_chunk(data)
            event = vad(torch.from_numpy(np.clip(chunk * 4.0, -1.0, 1.0)))

            if not speaking:
                if event is not None and "start" in event:
                    speaking = True
                    chunks.extend(recent_chunks)
                    chunks.append(chunk.copy())
                else:
                    recent_chunks.append(chunk.copy())
            else:
                chunks.append(chunk.copy())
                if event is not None and "end" in event:
                    break

    vad.reset_states()

    if not chunks:
        return None

    audio = np.concatenate(chunks)
    if len(audio) < int(SAMPLE_RATE * 0.2):
        return None
    logging.info(
        "Speech ended; transcribing %.2f seconds of audio.",
        len(audio) / SAMPLE_RATE,
    )
    return audio


def process_request(user_text, conversation):
    if not user_text:
        return "I didn't hear anything."

    history = conversation.get_previous_history()
    parsed = parse_command(user_text, history)
    command = parsed if isinstance(parsed, dict) else {"intent": "unknown"}

    if command.get("intent") in {
        "open_resource",
        "open_website",
        "open_system_settings",
        "system_control",
        "memory",
    }:
        result = execute(command)
        if result:
            return result
        return f"I couldn't process {command.get('query', 'that')}."

    web_result = None
    if should_search_web_first(user_text):
        web_result = search_web(user_text, history=history)
        if web_result.get("status") == "ok":
            return spoken_web_answer(web_result)
        if web_result.get("status") == "error":
            print(web_result.get("message", "Web search failed."))
        return web_search_failure_message(web_result)

    try:
        answer = ask_ai(user_text, history=history)
        if answer and answer.strip():
            return answer
    except Exception as exc:
        logging.exception("Local AI failed.")
        print(f"Local AI failed: {exc}")

    if web_result is None:
        web_result = search_web(user_text, history=history)
    if web_result.get("status") == "ok":
        return spoken_web_answer(web_result)

    return "I couldn't answer that right now."


mic_muted = False


def wait_for_command():
    if orb is not None and orb.stopped:
        return ""
    orb.set_state("Listening")
    audio = record_until_speech_end()
    if audio is None:
        return ""
    orb.set_state("Thinking")
    transcript = transcribe_audio(audio)
    if transcript and LOG_TRANSCRIPTS:
        logging.info("Transcribed speech: %s", transcript)
    else:
        logging.info("Speech audio produced no transcription.")
    return transcript


def wait_for_speech_to_finish():
    vad = VADIterator(
        vad_model,
        threshold=VAD_THRESHOLD,
        sampling_rate=SAMPLE_RATE,
        min_silence_duration_ms=END_OF_SPEECH_SILENCE_MS,
        speech_pad_ms=200,
    )
    chunks = []
    recent_chunks = deque(maxlen=7)
    speech_started = False

    try:
        with sd.InputStream(
            samplerate=MIC_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=MIC_CHUNK_SIZE,
            device=resolve_mic_device(),
        ) as stream:
            while is_speaking():
                if orb is not None and orb.stopped:
                    return None

                data, overflowed = stream.read(MIC_CHUNK_SIZE)
                if overflowed:
                    continue

                chunk = downsample_microphone_chunk(data)
                event = vad(torch.from_numpy(np.clip(chunk * 4.0, -1.0, 1.0)))
                if speech_started:
                    chunks.append(chunk)
                    if event is not None and "end" in event:
                        break
                elif event is not None and "start" in event:
                    speech_started = True
                    chunks.extend(recent_chunks)
                    chunks.append(chunk)
                    stop_speaking()
                    if orb is not None:
                        orb.set_state("Listening")
                else:
                    recent_chunks.append(chunk)

            if speech_started:
                while not (event is not None and "end" in event):
                    if orb is not None and orb.stopped:
                        return None
                    data, overflowed = stream.read(MIC_CHUNK_SIZE)
                    if overflowed:
                        continue
                    chunk = downsample_microphone_chunk(data)
                    chunks.append(chunk)
                    event = vad(torch.from_numpy(np.clip(chunk * 4.0, -1.0, 1.0)))
    finally:
        vad.reset_states()

    if not chunks:
        return None

    audio = np.concatenate(chunks)
    if len(audio) < int(SAMPLE_RATE * 0.2):
        return None
    return audio


tray = None


def acquire_single_instance():
    """Keeps simultaneous assistant launches from competing for the microphone."""
    global _instance_mutex_handle, _kernel32
    if sys.platform != "win32":
        return True

    import ctypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateMutexW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_bool,
        ctypes.c_wchar_p,
    ]
    _kernel32.CreateMutexW.restype = ctypes.c_void_p
    _kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    _kernel32.CloseHandle.restype = ctypes.c_bool
    ctypes.set_last_error(0)
    handle = _kernel32.CreateMutexW(None, True, "Local\\US-AI-DesktopAssistant")
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        if not _kernel32.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())
        logging.info("US AI is already running; ignoring duplicate launch.")
        return False
    _instance_mutex_handle = handle
    return True


def run_assistant(conversation, assistant_orb):
    print("\n==============================")
    print("   US AI BACKGROUND LISTENER")
    print("==============================")
    print("Listening continuously. Speak naturally; I will answer after you pause.")

    while not assistant_orb.stopped:
        try:
            if mic_muted:
                orb.set_state("Ready")
                time.sleep(0.2)
                continue

            orb.show("Listening")
            command_text = wait_for_command()
            if not command_text:
                print("No command was detected.")
                logging.info("No command transcription was produced.")
                orb.set_state("Ready")
                time.sleep(0.2)
                continue

            print(f"Command: {command_text}")
            if LOG_TRANSCRIPTS:
                logging.info("Processing transcribed command: %s", command_text)
            conversation.add_user(command_text)

            orb.set_state("Thinking")
            answer = process_request(command_text, conversation)
            logging.info("Assistant response ready.")
            while answer and not assistant_orb.stopped:
                print(f"US AI: {answer}")
                conversation.add_assistant(answer)
                orb.set_state("Speaking")
                # Listening to the microphone during playback can mistake
                # speaker echo or room noise for an interruption. Complete
                # the answer unless explicit barge-in mode is enabled.
                speak(answer, block=not ALLOW_BARGE_IN)
                logging.info("Speech playback started.")
                interrupted_audio = (
                    wait_for_speech_to_finish() if ALLOW_BARGE_IN else None
                )
                if interrupted_audio is None:
                    answer = None
                    break

                orb.set_state("Thinking")
                interruption_text = transcribe_audio(interrupted_audio)
                if not interruption_text:
                    answer = None
                    break

                print(f"Command: {interruption_text}")
                conversation.add_user(interruption_text)
                answer = process_request(interruption_text, conversation)

            if not assistant_orb.stopped:
                orb.set_state("Ready")

        except KeyboardInterrupt:
            print("\nUS AI background listener stopped.")
            stop_speaking()
            assistant_orb.close()
            orb.close()
            break
        except MicrophoneUnavailableError as exc:
            logging.error("%s", exc)
            print(f"Microphone unavailable: {exc}")
            orb.set_state("Ready")
            time.sleep(5)
        except sd.PortAudioError:
            logging.exception("Microphone stream failed; retrying in 5 seconds.")
            orb.set_state("Ready")
            time.sleep(5)
        except Exception as exc:
            logging.exception("Background assistant error.")
            print(f"Background assistant error: {exc}")
            stop_speaking()
            orb.set_state("Ready")
            time.sleep(1)


def main():
    global orb, tray
    if not acquire_single_instance():
        return

    conversation = ConversationManager()

    def handle_toggle_mic(muted):
        global mic_muted
        mic_muted = muted
        if tray is not None:
            tray.set_mic_muted(muted)
        if muted:
            stop_speaking()

    def handle_tray_open():
        if orb is not None:
            orb.show("Ready")

    def handle_tray_exit():
        if orb is not None:
            orb.close()

    orb = AssistantOrb()
    tray = AssistantTray(
        on_open_hud=handle_tray_open,
        on_exit=handle_tray_exit,
        on_toggle_mic=handle_toggle_mic,
    )
    tray.start()

    # Windows Console Control & Clean Shutdown Handler
    if sys.platform == "win32":
        import ctypes

        HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)

        def _win_ctrl_handler(ctrl_type):
            # Handles CTRL_CLOSE_EVENT (2), CTRL_LOGOFF_EVENT (5), CTRL_SHUTDOWN_EVENT (6)
            stop_speaking()
            if orb is not None:
                orb.close()
            if tray is not None:
                tray.stop()
            return True

        _handler_routine = HandlerRoutine(_win_ctrl_handler)
        ctypes.windll.kernel32.SetConsoleCtrlHandler(_handler_routine, True)

    assistant_thread = threading.Thread(
        target=run_assistant,
        args=(conversation, orb),
        name="assistant-audio-loop",
        daemon=True,
    )
    assistant_thread.start()
    try:
        orb.run()
    finally:
        orb.close()
        stop_speaking()
        if tray is not None:
            tray.stop()
        assistant_thread.join(timeout=2)
        if _instance_mutex_handle is not None:
            if not _kernel32.CloseHandle(_instance_mutex_handle):
                logging.error(
                    "Could not release the assistant instance mutex: %s",
                    ctypes.WinError(ctypes.get_last_error()),
                )


def handle_shutdown_signal(signum, _frame):
    if orb is not None:
        orb.close()
    if tray is not None:
        tray.stop()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    main()
