import os
import platform
import shutil
import subprocess


def open_application(app_name):
    app_name = app_name.lower().strip()

    windows_apps = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
    }
    linux_apps = {
        "chrome": ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"),
        "google chrome": ("google-chrome", "google-chrome-stable"),
        "notepad": ("gedit", "mousepad", "xed", "kate"),
        "calculator": ("gnome-calculator", "kcalc", "mate-calc"),
        "calc": ("gnome-calculator", "kcalc", "mate-calc"),
        "paint": ("pinta", "kolourpaint", "gpaint"),
    }

    system = platform.system()
    if system == "Windows":
        executable = windows_apps.get(app_name, app_name)
        resolved = shutil.which(executable)
        if not resolved and app_name in {"chrome", "google chrome"}:
            for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
                root = os.environ.get(variable)
                if not root:
                    continue
                candidate = os.path.join(
                    root,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                )
                if os.path.isfile(candidate):
                    resolved = candidate
                    break
        if not resolved and not os.path.isfile(executable):
            return f"I couldn't find {app_name} on this computer."
        command = [resolved or executable]
    elif system == "Linux":
        candidates = linux_apps.get(app_name, (app_name,))
        executable = None
        for candidate in candidates:
            executable = shutil.which(candidate)
            if executable:
                break
        if not executable:
            return f"I couldn't find {app_name} on this computer."
        command = [executable]
    else:
        return f"I don't know how to open {app_name} yet."

    try:
        subprocess.Popen(command)
        return f"Opening {app_name}."

    except OSError as exc:
        return f"I couldn't open {app_name}: {exc}"