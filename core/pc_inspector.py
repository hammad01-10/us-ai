import os
import platform
import shutil
import subprocess
from pathlib import Path

if platform.system() == "Windows":
    import winreg
else:
    winreg = None


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():

    return {
        "operating_system": platform.platform(),
        "os_version": platform.release(),
        "windows_version": (
            platform.version()
            if platform.system() == "Windows"
            else None
        ),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "computer_name": platform.node(),
        "python_version": platform.python_version(),
    }


# ============================================================
# INSTALLED PROGRAMS
# ============================================================

def get_installed_programs():

    if platform.system() != "Windows":
        return sorted({
            application["name"]
            for application in _get_linux_applications()
        })

    programs = set()

    registry_locations = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
    ]

    for root, path in registry_locations:

        try:

            key = winreg.OpenKey(root, path)

            count = winreg.QueryInfoKey(key)[0]

            for i in range(count):

                try:

                    subkey_name = winreg.EnumKey(key, i)

                    subkey = winreg.OpenKey(
                        key,
                        subkey_name
                    )

                    try:

                        name = winreg.QueryValueEx(
                            subkey,
                            "DisplayName"
                        )[0]

                        if name:
                            programs.add(name)

                    except FileNotFoundError:
                        pass

                    subkey.Close()

                except OSError:
                    pass

            key.Close()

        except OSError:
            pass

    return sorted(programs)


# ============================================================
# WINDOWS SHORTCUTS
# ============================================================

def get_shortcuts():

    if platform.system() == "Linux":
        return _get_linux_applications()

    locations = []
    if platform.system() == "Windows":
        user_profile = os.environ.get("USERPROFILE")
        app_data = os.environ.get("APPDATA")
        program_data = os.environ.get("PROGRAMDATA")
        if user_profile:
            locations.append(Path(user_profile) / "Desktop")
        if app_data:
            locations.append(
                Path(app_data) / "Microsoft/Windows/Start Menu/Programs"
            )
        if program_data:
            locations.append(
                Path(program_data) / "Microsoft/Windows/Start Menu/Programs"
            )

    shortcuts = []

    for location in locations:

        if not location.exists():
            continue

        try:

            for shortcut in location.rglob("*.lnk"):

                shortcuts.append({
                    "name": shortcut.stem,
                    "path": str(shortcut),
                    "type": "shortcut"
                })

        except PermissionError:
            pass

    return shortcuts


def _get_linux_applications():
    data_home = Path(
        os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    )
    locations = [
        data_home / "applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
    ]
    applications = {}

    for location in locations:
        if not location.is_dir():
            continue
        try:
            desktop_files = location.rglob("*.desktop")
            for desktop_file in desktop_files:
                name = None
                hidden = False
                no_display = False
                try:
                    with desktop_file.open(
                        encoding="utf-8",
                        errors="replace",
                    ) as file:
                        in_main_section = False
                        for line in file:
                            line = line.strip()
                            if line.startswith("["):
                                in_main_section = line == "[Desktop Entry]"
                                continue
                            if not in_main_section:
                                continue
                            if line.startswith("Name=") and name is None:
                                name = line[5:].strip()
                            elif line == "Hidden=true":
                                hidden = True
                            elif line == "NoDisplay=true":
                                no_display = True
                except OSError:
                    continue

                if name and not hidden and not no_display:
                    applications[str(desktop_file)] = {
                        "name": name,
                        "path": str(desktop_file),
                        "type": "linux_application",
                    }
        except OSError:
            continue

    return list(applications.values())


# ============================================================
# WINDOWS SYSTEM TOOLS
# ============================================================

def get_windows_tools():

    if platform.system() != "Windows":
        return []

    tools = []

    system_root = os.environ.get(
        "SystemRoot",
        r"C:\Windows"
    )

    system32 = Path(system_root) / "System32"

    if not system32.exists():
        return tools

    # Discover executable Windows tools.
    #
    # We are NOT defining commands here.
    # We are discovering what Windows actually provides.

    try:

        for file in system32.iterdir():

            if file.is_file() and file.suffix.lower() in [
                ".exe",
                ".msc",
                ".cpl"
            ]:

                tools.append({
                    "name": file.stem,
                    "path": str(file),
                    "type": "windows_system_resource"
                })

    except PermissionError:
        pass

    return tools


# ============================================================
# DRIVES
# ============================================================

def get_drives():

    drives = []

    if platform.system() != "Windows":
        paths = [Path("/")]
        for path in paths:
            try:
                total, used, free = shutil.disk_usage(path)
                drives.append({
                    "drive": str(path),
                    "total_gb": round(total / (1024 ** 3), 2),
                    "used_gb": round(used / (1024 ** 3), 2),
                    "free_gb": round(free / (1024 ** 3), 2),
                })
            except OSError:
                pass
        return drives

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":

        path = f"{letter}:\\"

        if os.path.exists(path):

            try:

                total, used, free = shutil.disk_usage(path)

                drives.append({
                    "drive": path,
                    "total_gb": round(
                        total / (1024 ** 3),
                        2
                    ),
                    "used_gb": round(
                        used / (1024 ** 3),
                        2
                    ),
                    "free_gb": round(
                        free / (1024 ** 3),
                        2
                    )
                })

            except OSError:
                pass

    return drives


# ============================================================
# NETWORK ADAPTERS
# ============================================================

def get_network_adapters():

    adapters = []

    if platform.system() != "Windows":
        return adapters

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetAdapter | "
                "Select-Object Name,InterfaceDescription,Status,MacAddress "
                "| ConvertTo-Json -Compress"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():

            import json

            data = json.loads(result.stdout)

            if isinstance(data, dict):
                data = [data]

            for adapter in data:

                adapters.append({
                    "name": adapter.get("Name"),
                    "description": adapter.get(
                        "InterfaceDescription"
                    ),
                    "status": adapter.get("Status"),
                    "mac": adapter.get("MacAddress")
                })

    except Exception:
        pass

    return adapters


# ============================================================
# PRINTERS
# ============================================================

def get_printers():

    printers = []

    if platform.system() != "Windows":
        return printers

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Printer | "
                "Select-Object Name,DriverName,PortName,PrinterStatus "
                "| ConvertTo-Json -Compress"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():

            import json

            data = json.loads(result.stdout)

            if isinstance(data, dict):
                data = [data]

            for printer in data:

                printers.append({
                    "name": printer.get("Name"),
                    "driver": printer.get("DriverName"),
                    "port": printer.get("PortName"),
                    "status": str(
                        printer.get("PrinterStatus")
                    )
                })

    except Exception:
        pass

    return printers


# ============================================================
# COMPLETE PC INSPECTION
# ============================================================

def inspect_pc():

    return {

        "system": get_system_info(),

        "installed_programs":
            get_installed_programs(),

        "shortcuts":
            get_shortcuts(),

        "windows_tools":
            get_windows_tools(),

        "drives":
            get_drives(),

        "network_adapters":
            get_network_adapters(),

        "printers":
            get_printers(),

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("==============================")
    print("       US AI PC INSPECTOR")
    print("==============================")

    data = inspect_pc()

    print()
    print("SYSTEM")
    print("------------------------------")

    for key, value in data["system"].items():
        print(f"{key}: {value}")

    print()
    print("DRIVES")
    print("------------------------------")

    for drive in data["drives"]:
        print(drive)

    print()
    print("NETWORK ADAPTERS")
    print("------------------------------")

    for adapter in data["network_adapters"]:
        print(adapter)

    print()
    print("PRINTERS")
    print("------------------------------")

    for printer in data["printers"]:
        print(printer)

    print()
    print("SHORTCUTS")
    print("------------------------------")

    print(
        f"Found {len(data['shortcuts'])} shortcuts."
    )

    for shortcut in data["shortcuts"]:
        print(
            f"- {shortcut['name']} "
            f"-> {shortcut['path']}"
        )

    print()
    print("WINDOWS SYSTEM RESOURCES")
    print("------------------------------")

    print(
        f"Found {len(data['windows_tools'])} "
        "Windows resources."
    )

    print()
    print("INSTALLED PROGRAMS")
    print("------------------------------")

    print(
        f"Found {len(data['installed_programs'])} programs."
    )

    for program in data["installed_programs"]:
        print("-", program)

    print()
    print("==============================")
    print("PC INSPECTION COMPLETE")
    print("==============================")