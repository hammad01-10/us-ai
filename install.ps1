param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\US-AI"),
    [switch]$NoAutostart,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-InstallerMessage {
    param([string]$Message)
    if (-not $Silent) {
        Write-Host $Message
    }
}

if ($env:OS -ne "Windows_NT") {
    throw "This installer supports Windows only."
}

if (-not (Test-Path (Join-Path $PSScriptRoot "voice\background_assistant.py"))) {
    throw "Run install.ps1 from the US-AI project folder."
}

$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
if ([string]::Equals(
    $InstallDir,
    [System.IO.Path]::GetFullPath($PSScriptRoot),
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw "Choose an installation folder separate from the project folder."
}

$BuildExe = Join-Path $PSScriptRoot "dist\US-AI.exe"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\US AI"
$shell = New-Object -ComObject WScript.Shell

if (Test-Path -LiteralPath $InstallDir) {
    $existingMarker = Join-Path $InstallDir ".us-ai-install-root"
    if (Test-Path -LiteralPath $InstallDir -PathType Container) {
        $existingItems = @(Get-ChildItem -LiteralPath $InstallDir -Force)
        if ($existingItems.Length -gt 0 -and -not (Test-Path -LiteralPath $existingMarker)) {
            throw "The installation folder already contains files and is not a US AI installation: $InstallDir"
        }
    }
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

if (Test-Path -LiteralPath $BuildExe) {
    Copy-Item -LiteralPath $BuildExe -Destination (Join-Path $InstallDir "US-AI.exe") -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "README.md") -Destination (Join-Path $InstallDir "README.md") -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "uninstall.ps1") -Destination (Join-Path $InstallDir "uninstall.ps1") -Force
    Set-Content -LiteralPath (Join-Path $InstallDir ".us-ai-install-root") -Value $InstallDir -Encoding UTF8

    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
    $launchShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "US AI.lnk"))
    $launchShortcut.TargetPath = (Join-Path $InstallDir "US-AI.exe")
    $launchShortcut.WorkingDirectory = $InstallDir
    $launchShortcut.Description = "Start the US AI desktop assistant"
    $launchShortcut.Save()

    $uninstallShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "Uninstall US AI.lnk"))
    $uninstallShortcut.TargetPath = (Join-Path $PSHOME "powershell.exe")
    $uninstallShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\uninstall.ps1`""
    $uninstallShortcut.WorkingDirectory = $InstallDir
    $uninstallShortcut.Description = "Uninstall US AI"
    $uninstallShortcut.Save()

    Write-InstallerMessage "US AI executable installed successfully."
    Write-InstallerMessage "Launch it from Start Menu > US AI > US AI."
    return
}

# Source fallback for a development install without a packaged executable.
$pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $pythonExe = $pythonCommand.Source
    $pythonArgs = @("-3")
} else {
    $pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    $pythonArgs = @()
}

if (-not $pythonExe) {
    throw "Python 3.10 or newer is required. Install Python from https://www.python.org/downloads/ and run this installer again."
}

$probe = "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
& $pythonExe @($pythonArgs + @("-c", $probe)) 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 or newer is required. Install Python from https://www.python.org/downloads/ and run this installer again."
}

$venvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
$venvPythonw = Join-Path $InstallDir ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $venvPython)) {
    & $pythonExe @($pythonArgs + @("-m", "venv", (Join-Path $InstallDir ".venv")))
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the US AI Python environment."
    }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not prepare pip." }
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install US AI Python dependencies." }

foreach ($directory in @("actions", "brain", "config", "core", "memory", "voice")) {
    $source = Join-Path $PSScriptRoot $directory
    $destination = Join-Path $InstallDir $directory
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Recurse -File |
        Where-Object {
            $_.FullName -notmatch '[\\/](?:__pycache__|\.venv)[\\/]'
            $_.Extension -notin @(".pyc", ".wav")
        } |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($source.Length).TrimStart('\\', '/')
            $targetPath = Join-Path $destination $relativePath
            $targetParent = Split-Path -Parent $targetPath
            New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Force
        }
}

foreach ($file in @("README.md", "install_service.py", "uninstall_service.py", "uninstall.ps1")) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination (Join-Path $InstallDir $file) -Force
}
Set-Content -LiteralPath (Join-Path $InstallDir ".us-ai-install-root") -Value $InstallDir -Encoding UTF8

New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
$launchShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "US AI.lnk"))
$launchShortcut.TargetPath = $venvPythonw
$launchShortcut.Arguments = "-m voice.background_assistant"
$launchShortcut.WorkingDirectory = $InstallDir
$launchShortcut.Description = "Start the US AI desktop assistant"
$launchShortcut.Save()

$uninstallShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "Uninstall US AI.lnk"))
$uninstallShortcut.TargetPath = (Join-Path $PSHOME "powershell.exe")
$uninstallShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$InstallDir\uninstall.ps1`""
$uninstallShortcut.WorkingDirectory = $InstallDir
$uninstallShortcut.Description = "Uninstall US AI"
$uninstallShortcut.Save()

if (-not $NoAutostart -and -not $Silent) {
    Write-Warning "Autostart is not enabled automatically. Run python install_service.py from the project folder if you want it enabled."
}

Write-InstallerMessage "US AI source install is complete."
Write-InstallerMessage "Launch it from Start Menu > US AI > US AI."
