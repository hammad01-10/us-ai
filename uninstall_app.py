"""Windows uninstaller for US AI; deliberately has no PowerShell dependency."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    install_dir = Path(sys.executable).resolve().parent
    menu_dir = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "US AI"
    if sys.platform == "win32":
        import winreg

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\US-AI")
        except FileNotFoundError:
            pass
    shutil.rmtree(menu_dir, ignore_errors=True)
    # A running executable cannot remove its own directory; cmd is only used
    # as a tiny delayed cleanup process, not as an installation dependency.
    cleanup = Path(os.environ.get("TEMP", install_dir)) / "us-ai-uninstall.cmd"
    cleanup.write_text(f'@echo off\ntimeout /t 1 /nobreak >nul\nrmdir /s /q "{install_dir}"\ndel "%~f0"\n', encoding="utf-8")
    subprocess.Popen(["cmd.exe", "/c", str(cleanup)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


if __name__ == "__main__":
    main()
