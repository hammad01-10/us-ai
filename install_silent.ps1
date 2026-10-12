param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\US-AI"),
    [switch]$NoAutostart
)

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "install.ps1") -InstallDir $InstallDir -NoAutostart:$NoAutostart -Silent
