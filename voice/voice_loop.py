import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from voice.tts import speak

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
DEVICE = None

print("Loading US AI speech model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("\n==============================")
print("       US AI VOICE LOOP")
print("==============================")
print("US AI is ready.")

input("\nPress ENTER, then speak for 5 seconds...")

print("Listening...")

audio = sd.rec(
    int(RECORD_SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="float32",
    device=DEVICE
)

sd.wait()

print("Processing speech...")

audio = audio.flatten()

segments, info = model.transcribe(
    audio,
    language="en"
)

text = " ".join(
    segment.text.strip()
    for segment in segments
).strip()

print("\nYou said:")
print(text)

if text:
    speak(f"You said: {text}")
else:
    speak("I didn't hear anything.")