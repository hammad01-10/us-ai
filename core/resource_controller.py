import os
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from actions.desktop import open_application


def open_resource(resource):
    if not resource:
        return {
            "status": "error",
            "message": "No resource was provided.",
        }

    resource_type = resource.get("type")
    path = resource.get("path")
    name = resource.get("name", "resource")

    if resource_type in {"shortcut", "linux_application"}:
        if not path or not os.path.exists(path):
            return {
                "status": "not_found",
                "message": "The resource is no longer available.",
            }

        try:
            if platform.system() == "Windows":
                subprocess.Popen(["explorer.exe", path])
            elif resource_type == "linux_application":
                launcher = shutil.which("gtk-launch")
                if launcher:
                    subprocess.Popen([launcher, Path(path).stem])
                else:
                    _launch_desktop_file(path)
            else:
                _open_with_desktop(path)

            return {
                "status": "opened",
                "message": f"Opening {name}.",
            }
        except (OSError, ValueError) as exc:
            return {
                "status": "error",
                "message": f"I couldn't open {name}: {exc}",
            }

    if resource_type == "windows_system_resource":
        if not path or not os.path.exists(path):
            return {
                "status": "not_found",
                "message": "The Windows resource is no longer available.",
            }

        try:
            subprocess.Popen([path])
            return {
                "status": "opened",
                "message": f"Opening {name}.",
            }
        except OSError as exc:
            return {
                "status": "error",
                "message": f"I couldn't open {name}: {exc}",
            }

    if resource_type == "installed_program":
        message = open_application(name)
        if message.startswith("Opening "):
            return {"status": "opened", "message": message}
        return {"status": "error", "message": message}

    return {
        "status": "unsupported",
        "message": f"I don't know how to open {name} yet.",
    }


def _open_with_desktop(path):
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", path])
    elif system == "Linux":
        opener = shutil.which("xdg-open")
        if not opener:
            raise OSError("xdg-open is not installed.")
        subprocess.Popen([opener, path])
    else:
        os.startfile(path)


def _launch_desktop_file(path):
    exec_line = ""
    with open(path, encoding="utf-8", errors="replace") as desktop_file:
        for line in desktop_file:
            if line.startswith("Exec="):
                exec_line = line[len("Exec="):].strip()
                break

    if not exec_line:
        raise ValueError("Desktop launcher has no Exec command.")

    arguments = []
    for argument in shlex.split(exec_line):
        if argument in {"%f", "%F", "%u", "%U", "%i", "%c", "%k"}:
            continue
        argument = re.sub(r"%[fFuUick]", "", argument)
        if argument:
            arguments.append(argument)

    if not arguments:
        raise ValueError("Desktop launcher has an empty Exec command.")

    subprocess.Popen(arguments)


if __name__ == "__main__":
    example = {
        "name": "System Information",
        "type": "shortcut",
        "path": (
            r"C:\ProgramData\Microsoft\Windows"
            r"\Start Menu\Programs\Administrative Tools"
            r"\System Information.lnk"
        ),
    }
    print(open_resource(example))
