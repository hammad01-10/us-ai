import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

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

print("\nUS AI is ready.")
input("Press ENTER and speak for 5 seconds...")

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

# Convert stereo/2D audio to a 1D array
audio = audio.flatten()

segments, info = model.transcribe(
    audio,
    language="en"
)

text = " ".join(segment.text.strip() for segment in segments)

print("\nUS AI heard:")
print(text)