import sounddevice as sd
import wave

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
OUTPUT_FILE = "voice_test.wav"
DEVICE = None

print("US AI microphone test")
print("Get ready...")
input("Press ENTER, then speak for 5 seconds...")

print("Listening...")

audio = sd.rec(
    int(RECORD_SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="int16",
    device=DEVICE
)

sd.wait()

with wave.open(OUTPUT_FILE, "wb") as wav:
    wav.setnchannels(CHANNELS)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(audio.tobytes())

print(f"Recording saved as {OUTPUT_FILE}")