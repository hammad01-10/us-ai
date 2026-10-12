$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual environment not found. Create it and install requirements.txt before running the assistant."
}

Push-Location $projectRoot
try {
    & $python -m voice.background_assistant
    if ($LASTEXITCODE -ne 0) {
        throw "US AI exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
