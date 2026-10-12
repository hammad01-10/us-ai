## Windows installer

On Windows, run the packaged `installer\setup.exe` directly. The installer is a native Windows GUI and does not require PowerShell or Python on the target PC.

For a source install during development, run `install.ps1` from the project folder in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

The installer creates a clean install under `%LOCALAPPDATA%\Programs\US-AI`, adds a launch shortcut in the Start Menu, and keeps the uninstall script in the installed folder. It does not prompt for extra optional setup steps such as model downloads or autostart configuration during the normal install flow. For unattended installs, use `install_silent.ps1` or `powershell -ExecutionPolicy Bypass -File .\install.ps1 -Silent`.

To remove the app, use **Start Menu > US AI > Uninstall US AI**, or run `uninstall.ps1` from the installed folder. Uninstalling preserves personal assistant memory in `%USERPROFILE%\.us-ai`.

## Build the Windows installer

Build the app executable and the self-contained Windows installer with:

```powershell
.\build_exe.ps1
.\build_installer.ps1
```

The installer is created at `installer\setup.exe`. It installs the app under `%LOCALAPPDATA%\Programs\US-AI`, creates Start Menu launch and uninstall shortcuts, and registers a standard per-user uninstall entry. It does not require Python or a separate installer framework on the target PC. To remove the app, use **Start Menu > US AI > Uninstall US AI** or Windows **Installed apps**.

The no-PowerShell installer can be rebuilt with `python build_installer.py` after `dist\US-AI.exe` exists. The resulting `setup.exe` contains the packaged assistant and compiled uninstaller, so the recipient does not need this project folder or any supporting files.

The assistant uses the local Ollama service and the `llama3.2:3b` model for AI responses. It continuously listens through the selected microphone while unmuted, using voice activity detection to detect speech and wait one second after you stop before responding. Startup and voice diagnostics are written to `%USERPROFILE%\.us-ai\assistant.log`.

The assistant continuously listens while its microphone is unmuted. Speak naturally; it waits for about one second of silence before transcribing and responding. No wake phrase is required. The desktop companion is a small animated orb.

The packaged `setup.exe` opens a Jarvis-style installation wizard where you can choose the install folder, see installation progress, and launch US AI after setup. When rebuilding, run `build_exe.ps1` first, then `python build_installer.py` to include the latest assistant.

The executable itself is built at `dist\US-AI.exe`. The build uses PyInstaller and Windows IExpress; IExpress is included with Windows. A portable folder bundle is also created at `installer\US-AI-Portable`.

## Capabilities & Controls
