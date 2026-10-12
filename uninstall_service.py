import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.autostart import disable_autostart, is_autostart_enabled


def uninstall_service():
    result = disable_autostart()
    print("=" * 50)
    print("          US AI AUTOSTART REMOVAL")
    print("=" * 50)
    print(result)
    print(f"Autostart Active: {is_autostart_enabled()}")
    print("=" * 50)
    return result


if __name__ == "__main__":
    uninstall_service()
