import getpass
import os
import platform
import subprocess
import sys
from pathlib import Path

if platform.system() == "Windows":
    import winreg
else:
    winreg = None

PROJECT_DIR = Path(__file__).resolve().parent.parent
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "US_AI_Assistant"


def get_assistant_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return PROJECT_DIR / "voice" / "background_assistant.py"


ASSISTANT_PATH = get_assistant_path()


def get_pythonw_executable():
    """Returns path to pythonw.exe (windowless python) to avoid showing a console window on startup."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    python = Path(sys.executable)
    # Check in venv Scripts
    pythonw = python.with_name("pythonw.exe")
    if pythonw.is_file():
        return pythonw
    # Check parent or system
    sys_pythonw = Path(sys.prefix) / "pythonw.exe"
    if sys_pythonw.is_file():
        return sys_pythonw
    return python


def enable_autostart():
    """
    Configures the assistant to automatically launch silently in the background
    at Windows logon or Linux desktop session start.
    """
    system = platform.system()

    if system == "Windows":
        pythonw = get_pythonw_executable()
        if getattr(sys, "frozen", False):
            command = f'"{pythonw}"'
        else:
            command = f'"{pythonw}" "{ASSISTANT_PATH}"'

        # 1. Register in Windows Registry Run key (standard per-user autostart)
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        except OSError as exc:
            return f"Failed to register Windows Run key: {exc}"

        # 2. Also ensure any old Task Scheduler entries or legacy batch files are cleaned up
        try:
            subprocess.run(
                ["schtasks.exe", "/Delete", "/TN", "US AI Assistant", "/F"],
                capture_output=True,
                text=True,
            )
        except Exception:
            pass

        return f"Successfully enabled Windows autostart: {command}"

    elif system == "Linux":
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        autostart_dir = config_home / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / "us-ai.desktop"

        assistant_target = get_assistant_path()
        if getattr(sys, "frozen", False):
            command = f'"{sys.executable}"'
        else:
            command = f'"{sys.executable}" "{assistant_target}"'

        content = f"""[Desktop Entry]
Type=Application
Name=US AI Assistant
Comment=US AI Desktop Voice Assistant
Exec={command}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        desktop_file.write_text(content, encoding="utf-8")
        return f"Successfully enabled Linux desktop autostart: {desktop_file}"

    return f"Autostart is not supported on {system}."


def disable_autostart():
    """Removes autostart configuration for the assistant."""
    system = platform.system()

    if system == "Windows":
        removed = False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_RUN_KEY,
                0,
                winreg.KEY_ALL_ACCESS,
            ) as key:
                winreg.DeleteValue(key, APP_NAME)
                removed = True
        except FileNotFoundError:
            pass
        except OSError as exc:
            return f"Failed to remove Windows Run key: {exc}"

        # Clean Task Scheduler if any
        try:
            subprocess.run(
                ["schtasks.exe", "/Delete", "/TN", "US AI Assistant", "/F"],
                capture_output=True,
                text=True,
            )
        except Exception:
            pass

        if removed:
            return "Successfully disabled Windows autostart."
        return "Windows autostart was not configured."

    elif system == "Linux":
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        desktop_file = config_home / "autostart" / "us-ai.desktop"
        if desktop_file.exists():
            desktop_file.unlink()
            return "Successfully disabled Linux autostart."
        return "Linux autostart was not configured."

    return f"Autostart is not supported on {system}."


def is_autostart_enabled():
    """Checks whether the assistant is currently configured to autostart."""
    system = platform.system()

    if system == "Windows":
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REG_RUN_KEY,
                0,
                winreg.KEY_READ,
            ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except (FileNotFoundError, OSError):
            return False

    elif system == "Linux":
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        desktop_file = config_home / "autostart" / "us-ai.desktop"
        return desktop_file.exists()

    return False
