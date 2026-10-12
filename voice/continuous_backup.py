import time
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from brain.brain import ask_ai
from brain.command_parser import parse_command
from brain.conversation import ConversationManager
from core.controller import execute
from voice.tts import speak, stop_speaking, is_speaking


# ============================================================
# AUDIO
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1

# Current working microphone
DEVICE = None

CHUNK_DURATION = 0.10
CHUNK_SIZE = int(
    SAMPLE_RATE * CHUNK_DURATION
)


# ============================================================
# NORMAL LISTENING
# ============================================================

SILENCE_THRESHOLD = 0.015
END_SILENCE_DURATION = 0.8
MIN_SPEECH_DURATION = 0.25


# ============================================================
# BARGE-IN
# ============================================================

MIN_INTERRUPT_THRESHOLD = 0.018

NOISE_MULTIPLIER = 3.0

# Number of consecutive chunks required.
#
# 0.10 sec per chunk
# 4 chunks = about 0.40 sec
#
INTERRUPT_CHUNKS_REQUIRED = 4

# Ignore microphone immediately after TTS starts
TTS_PROTECTION_TIME = 0.50


# ============================================================
# RMS
# ============================================================

def get_rms(audio):

    if len(audio) == 0:
        return 0.0

    return float(
        np.sqrt(
            np.mean(
                np.square(audio)
            )
        )
    )


# ============================================================
# NOISE CALIBRATION
# ============================================================

def calibrate_noise():

    print()
    print("🎧 Calibrating microphone noise...")
    print("Please remain silent.")

    readings = []

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=DEVICE,
            blocksize=CHUNK_SIZE
        ) as stream:

            start = time.time()

            while (
                time.time() - start
                < 1.5
            ):

                audio, overflowed = stream.read(
                    CHUNK_SIZE
                )

                audio = audio[:, 0]

                readings.append(
                    get_rms(audio)
                )

    except Exception as e:

        print(
            "Noise calibration error:",
            e
        )

        return 0.01

    if not readings:

        return 0.01

    noise_floor = float(
        np.percentile(
            readings,
            90
        )
    )

    print(
        f"🎧 Noise floor: {noise_floor:.4f}"
    )

    return noise_floor


# ============================================================
# INTERRUPT DETECTOR
# ============================================================

def detect_interrupt(
    stop_event,
    tts_start_time
):

    """
    Detect genuine user speech while US AI speaks.

    A single loud microphone sample is ignored.

    Speech must remain above the calculated threshold
    for several consecutive chunks.
    """

    noise_floor = calibrate_noise()

    interrupt_threshold = max(
        MIN_INTERRUPT_THRESHOLD,
        noise_floor * NOISE_MULTIPLIER
    )

    print(
        f"🎚️ Interrupt threshold: "
        f"{interrupt_threshold:.4f}"
    )

    consecutive_chunks = 0

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=DEVICE,
            blocksize=CHUNK_SIZE
        ) as stream:

            while not stop_event.is_set():

                audio, overflowed = stream.read(
                    CHUNK_SIZE
                )

                audio = audio[:, 0]

                # --------------------------------------------
                # Protection period
                # --------------------------------------------

                if (
                    time.time() - tts_start_time
                    < TTS_PROTECTION_TIME
                ):

                    consecutive_chunks = 0

                    continue

                volume = get_rms(audio)

                # --------------------------------------------
                # Possible speech
                # --------------------------------------------

                if volume >= interrupt_threshold:

                    consecutive_chunks += 1

                else:

                    consecutive_chunks = 0

                # --------------------------------------------
                # Sustained speech confirmed
                # --------------------------------------------

                if (
                    consecutive_chunks
                    >= INTERRUPT_CHUNKS_REQUIRED
                ):

                    print()
                    print(
                        "🛑 User interruption detected."
                    )

                    stop_speaking()

                    stop_event.set()

                    return

    except Exception as e:

        print(
            "Interrupt detector error:",
            e
        )


# ============================================================
# LISTEN UNTIL USER FINISHES
# ============================================================

def listen_until_finished():

    print("🎤 Waiting for speech...")

    chunks = []

    speech_started = False

    speech_start_time = None

    silence_start_time = None

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=DEVICE,
        blocksize=CHUNK_SIZE
    ) as stream:

        while True:

            audio, overflowed = stream.read(
                CHUNK_SIZE
            )

            audio = audio[:, 0]

            volume = get_rms(audio)

            # --------------------------------------------
            # Waiting for speech
            # --------------------------------------------

            if not speech_started:

                if volume >= SILENCE_THRESHOLD:

                    speech_started = True

                    speech_start_time = time.time()

                    silence_start_time = None

                    chunks.append(
                        audio.copy()
                    )

                    print(
                        "🎙️ Listening..."
                    )

                continue

            # --------------------------------------------
            # Recording speech
            # --------------------------------------------

            chunks.append(
                audio.copy()
            )

            if volume < SILENCE_THRESHOLD:

                if silence_start_time is None:

                    silence_start_time = time.time()

                silence_duration = (
                    time.time()
                    - silence_start_time
                )

                if (
                    silence_duration
                    >= END_SILENCE_DURATION
                ):

                    total_duration = (
                        time.time()
                        - speech_start_time
                    )

                    if (
                        total_duration
                        >= MIN_SPEECH_DURATION
                    ):

                        break

            else:

                silence_start_time = None

    if not chunks:

        return None

    return np.concatenate(
        chunks
    )


# ============================================================
# SPEAK + BARGE-IN
# ============================================================

def speak_with_interrupt(answer):

    stop_event = threading.Event()

    print()
    print("🔊 US AI speaking...")

    # Record the exact moment TTS starts
    tts_start_time = time.time()

    # Start TTS
    speak(answer)

    # Start microphone monitor
    interrupt_thread = threading.Thread(
        target=detect_interrupt,
        args=(
            stop_event,
            tts_start_time
        ),
        daemon=True
    )

    interrupt_thread.start()

    # --------------------------------------------
    # Wait for speech to finish
    # --------------------------------------------

    while is_speaking():

        if stop_event.is_set():

            break

        time.sleep(0.05)

    # --------------------------------------------
    # Stop microphone monitor
    # --------------------------------------------

    stop_event.set()

    interrupt_thread.join(
        timeout=0.5
    )

    print()

    print(
        "🔇 Speech finished."
    )


# ============================================================
# START
# ============================================================

print()
print("==============================")
print("        LOADING US AI")
print("==============================")

print()
print("Loading Whisper...")

whisper = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

conversation = ConversationManager(
    max_turns=10
)

print()
print("==============================")
print("        US AI ONLINE")
print("==============================")
print("Voice + AI + PC Control")
print("Conversation + Interruptible Speech")
print("==============================")
print()


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    try:

        # --------------------------------------------
        # LISTEN
        # --------------------------------------------

        audio = listen_until_finished()

        if audio is None:

            continue

        print()
        print("🧠 Processing speech...")

        segments, info = whisper.transcribe(
            audio,
            language="en"
        )

        user_text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        if not user_text:

            continue

        print()
        print("You:", user_text)

        # --------------------------------------------
        # CONVERSATION
        # --------------------------------------------

        conversation.add_user(
            user_text
        )

        history = conversation.get_history()

        # --------------------------------------------
        # UNDERSTAND
        # --------------------------------------------

        print()
        print(
            "US AI is understanding..."
        )

        request = parse_command(
            user_text,
            history
        )

        print()
        print(
            "Command:",
            request
        )

        # --------------------------------------------
        # EXECUTE
        # --------------------------------------------

        result = execute(
            request
        )

        # --------------------------------------------
        # AI
        # --------------------------------------------

        if result is None:

            print()
            print(
                "US AI is thinking..."
            )

            answer = ask_ai(
                request.get(
                    "query",
                    user_text
                ),
                history
            )

        else:

            answer = result

        # --------------------------------------------
        # STORE
        # --------------------------------------------

        conversation.add_assistant(
            answer
        )

        print()
        print(
            "US AI:",
            answer
        )

        # --------------------------------------------
        # SPEAK
        # --------------------------------------------

        speak_with_interrupt(
            answer
        )

        print()

    except KeyboardInterrupt:

        stop_speaking()

        print()
        print(
            "US AI stopped."
        )

        break

    except Exception as e:

        stop_speaking()

        print()
        print(
            "US AI encountered an error:"
        )

        print(e)

        print()