param(
    [switch]$SkipPyInstaller
)

$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    $pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
        $pythonArgs = @("-3")
    } else {
        $python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
        $pythonArgs = @()
    }
}

if (-not $python) {
    throw "Python 3.10 or newer is required. Create a virtual environment first or install Python from https://www.python.org/downloads/."
}

if (-not $SkipPyInstaller) {
    & $python @($pythonArgs + @("-m", "pip", "install", "pyinstaller"))
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller could not be installed."
    }
}

$pyInstallerRunner = $python
if (-not $SkipPyInstaller) {
    $pyInstallerRunner = (Join-Path $projectRoot ".venv\Scripts\python.exe")
    if (-not (Test-Path -LiteralPath $pyInstallerRunner)) {
        $pyInstallerRunner = $python
    }
}

$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$specDir = Join-Path $projectRoot "build"

New-Item -ItemType Directory -Path $distDir -Force | Out-Null
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null

& $pyInstallerRunner -m PyInstaller `
    --noconsole `
    --onefile `
    --clean `
    --name "US-AI" `
    --distpath $distDir `
    --workpath $buildDir `
    --specpath $specDir `
    --add-data "$projectRoot\voice\models;voice/models" `
    --add-data "$projectRoot\voice\tts_output.wav;voice" `
    --hidden-import "sounddevice" `
    --hidden-import "silero_vad" `
    --hidden-import "faster_whisper" `
    --hidden-import "pystray" `
    --hidden-import "PIL" `
    --hidden-import "torch" `
    --collect-all "silero_vad" `
    --collect-all "faster_whisper" `
    "voice\background_assistant.py"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed while building the US AI executable."
}

Write-Host "Executable built successfully: $distDir\US-AI.exe"
