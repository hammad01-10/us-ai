"""Build the self-contained no-PowerShell US AI installer."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
OUTPUT = ROOT / "installer"
PYINSTALLER = [sys.executable, "-m", "PyInstaller"]


def build_uninstaller() -> Path:
    subprocess.run(PYINSTALLER + ["--noconfirm", "--clean", "--onefile", "--windowed", "--name", "uninstall", "--distpath", str(OUTPUT), "--workpath", str(ROOT / "build" / "uninstaller"), str(ROOT / "uninstall_app.py")], check=True)
    return OUTPUT / "uninstall.exe"


def main() -> None:
    app = DIST / "US-AI.exe"
    if not app.is_file():
        raise SystemExit("Build dist\\US-AI.exe first.")
    OUTPUT.mkdir(exist_ok=True)
    uninstall = build_uninstaller()
    subprocess.run(PYINSTALLER + ["--noconfirm", "--clean", "--onefile", "--windowed", "--name", "setup", "--distpath", str(OUTPUT), "--workpath", str(ROOT / "build" / "setup"), "--add-data", f"{app};payload", "--add-data", f"{uninstall};payload", str(ROOT / "setup_installer.py")], check=True)
    print(f"Installer created: {OUTPUT / 'setup.exe'}")


if __name__ == "__main__":
    main()
