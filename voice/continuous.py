import sys
import time
import numpy as np
import sounddevice as sd
import torch

from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, VADIterator

from brain.brain import ask_ai
from brain.command_parser import parse_command
from brain.conversation import ConversationManager
from core.controller import execute
from voice.tts import speak, stop_speaking, is_speaking


SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 512

MAX_RECORDING_SECONDS = 30
MIN_SILENCE_MS = 1200
SPEECH_PAD_MS = 200
VAD_THRESHOLD = 0.5

WHISPER_MODEL = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

MIC_DEVICE = None


print("Loading Silero VAD...")

vad_model = load_silero_vad()

print("Silero VAD loaded.")

print("Loading Whisper...")

whisper = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE
)

print("Whisper loaded.")


def create_vad():

    return VADIterator(
        vad_model,
        threshold=VAD_THRESHOLD,
        sampling_rate=SAMPLE_RATE,
        min_silence_duration_ms=MIN_SILENCE_MS,
        speech_pad_ms=SPEECH_PAD_MS
    )


def record_user_turn(initial_chunks=None):

    vad = create_vad()

    audio_chunks = []

    if initial_chunks:
        audio_chunks.extend(initial_chunks)

    speaking = bool(initial_chunks)

    start_time = time.monotonic()

    print()
    print("🎤 Waiting for speech...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        device=MIC_DEVICE
    ) as stream:

        while True:

            if time.monotonic() - start_time >= MAX_RECORDING_SECONDS:

                print("⏱️ Maximum recording time reached.")

                break

            data, overflowed = stream.read(CHUNK_SIZE)

            if overflowed:
                print("⚠️ Microphone buffer overflow.")

            chunk = np.asarray(
                data[:, 0],
                dtype=np.float32
            ).copy()

            event = vad(
                torch.from_numpy(chunk)
            )

            if not speaking:

                if event is not None and "start" in event:

                    speaking = True

                    print("🗣️ Speech detected.")

                    audio_chunks.append(chunk)

            else:

                audio_chunks.append(chunk)

                if event is not None and "end" in event:

                    print("🛑 Speech finished.")

                    break

    vad.reset_states()

    if not audio_chunks:
        return None

    audio = np.concatenate(audio_chunks)

    if len(audio) < int(SAMPLE_RATE * 0.2):
        return None

    return audio


def transcribe_audio(audio):

    if audio is None:
        return ""

    print()
    print("🧠 Transcribing...")

    segments, info = whisper.transcribe(
        audio,
        language="en",
        beam_size=5,
        best_of=5,
        temperature=0,
        vad_filter=False,
        condition_on_previous_text=False
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    return text.strip()


def listen_for_interruption():

    vad = create_vad()

    interruption_chunks = []
    speech_started = False

    print("🎧 Listening for user interruption...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        device=MIC_DEVICE
    ) as stream:

        while is_speaking():

            data, overflowed = stream.read(CHUNK_SIZE)

            if overflowed:
                continue

            chunk = np.asarray(
                data[:, 0],
                dtype=np.float32
            ).copy()

            event = vad(
                torch.from_numpy(chunk)
            )

            if not speech_started:

                if event is not None and "start" in event:

                    speech_started = True

                    print()
                    print("🛑 User started speaking.")

                    interruption_chunks.append(chunk)

            else:

                interruption_chunks.append(chunk)

    vad.reset_states()

    if speech_started:
        return interruption_chunks

    return None


def speak_with_interrupt(text):

    if not text:
        return None

    speak(text)

    interruption = listen_for_interruption()

    if interruption:

        stop_speaking()

        time.sleep(0.05)

        return interruption

    return None


def process_user_audio(audio, conversation):

    text = transcribe_audio(audio)

    if not text:
        return None

    print()
    print("You:", text)

    conversation.add_user(text)

    history = conversation.get_previous_history()

    command = parse_command(
        text,
        history
    )

    answer = execute(command)

    if answer is None:

        answer = ask_ai(
            command.get("query", text),
            history
        )

    if not answer:

        answer = "I'm sorry, I couldn't come up with an answer."

    print()
    print("US AI:", answer)

    conversation.add_assistant(answer)

    return answer


def main():

    conversation = ConversationManager()

    print()
    print("==============================")
    print("        US AI VOICE")
    print("==============================")
    print()
    print("Streaming Silero VAD active.")
    print("Speak naturally.")
    print("US AI will wait for your speech to finish.")
    print("You can interrupt US AI while it is speaking.")
    print("Ctrl+C to stop.")
    print()

    while True:

        try:

            audio = record_user_turn()

            if audio is None:
                continue

            answer = process_user_audio(
                audio,
                conversation
            )

            if not answer:
                continue

            print()
            print("🔊 US AI speaking...")

            interrupted_audio = speak_with_interrupt(
                answer
            )

            if interrupted_audio:

                print("🎤 Capturing your complete interruption...")

                complete_audio = record_user_turn(
                    initial_chunks=interrupted_audio
                )

                if complete_audio is None:
                    continue

                new_answer = process_user_audio(
                    complete_audio,
                    conversation
                )

                if new_answer:

                    print()
                    print("🔊 US AI speaking...")

                    speak_with_interrupt(
                        new_answer
                    )

        except KeyboardInterrupt:

            print()
            print("US AI stopped.")

            stop_speaking()

            break

        except Exception as e:

            print()
            print("⚠️ US AI error:")
            print(type(e).__name__, str(e))

            stop_speaking()

            time.sleep(1)


if __name__ == "__main__":
    main()
