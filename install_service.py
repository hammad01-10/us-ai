import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.autostart import enable_autostart, is_autostart_enabled


def install_service():
    result = enable_autostart()
    print("=" * 50)
    print("          US AI AUTOSTART INSTALLATION")
    print("=" * 50)
    print(result)
    print(f"Autostart Active: {is_autostart_enabled()}")
    print("US AI will now automatically run silently in the background")
    print("whenever Windows starts or you log in.")
    print("=" * 50)
    return result


if __name__ == "__main__":
    install_service()
