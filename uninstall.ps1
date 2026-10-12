$ErrorActionPreference = "Stop"

$installDir = [System.IO.Path]::GetFullPath($PSScriptRoot)
$marker = Join-Path $installDir ".us-ai-install-root"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\US AI"
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\US-AI"

if (-not (Test-Path -LiteralPath $marker)) {
    throw "This folder is not marked as a US AI installation; refusing to remove it."
}

$recordedPath = (Get-Content -LiteralPath $marker -Raw).Trim()
if (-not [string]::Equals(
    [System.IO.Path]::GetFullPath($recordedPath),
    $installDir,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw "The installation marker does not match this folder; refusing to remove it."
}

$python = Join-Path $installDir ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $python) {
    & $python -c "from core.autostart import disable_autostart; print(disable_autostart())"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not remove US AI autostart. No installed files were removed."
    }
}

if (Test-Path -LiteralPath $startMenuDir) {
    Remove-Item -LiteralPath $startMenuDir -Recurse -Force
}

if (Test-Path -LiteralPath $uninstallKey) {
    Remove-Item -LiteralPath $uninstallKey -Recurse -Force
}

Write-Host "Removing US AI from $installDir"
Remove-Item -LiteralPath $installDir -Recurse -Force
Write-Host "US AI was uninstalled. Your personal memory in $HOME\.us-ai was preserved."
