from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_RECORD_SECONDS = 5
DEFAULT_MIC_DEVICE = None

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

WEB_SEARCH_TIMEOUT = 12
OLLAMA_TIMEOUT = 60
LOG_TRANSCRIPTS = False

# Complete each spoken answer by default. Barge-in can be enabled later for
# users with headphones or a microphone that does not capture speaker audio.
ALLOW_BARGE_IN = False

AUTOSTART_LINK_NAME = "US AI Startup.cmd"
