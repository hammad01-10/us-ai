param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "installer")
)

$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$outputPath = [System.IO.Path]::GetFullPath($OutputDir)
$buildExe = Join-Path $projectRoot "dist\US-AI.exe"
$readme = Join-Path $projectRoot "README.md"
$uninstaller = Join-Path $projectRoot "uninstall.ps1"

if (-not (Test-Path -LiteralPath $buildExe -PathType Leaf)) {
    throw "Build the executable first with .\build_exe.ps1."
}

if (-not (Test-Path -LiteralPath $readme -PathType Leaf)) {
    throw "README.md is missing from the project folder."
}

if (-not (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
    throw "uninstall.ps1 is missing from the project folder."
}

$iexpress = Join-Path $env:WINDIR "System32\iexpress.exe"
if (-not (Test-Path -LiteralPath $iexpress -PathType Leaf)) {
    throw "IExpress is required to create setup.exe, but was not found at $iexpress."
}

New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

$portableDir = Join-Path $outputPath "US-AI-Portable"
New-Item -ItemType Directory -Path $portableDir -Force | Out-Null
Copy-Item -LiteralPath $buildExe -Destination (Join-Path $portableDir "US-AI.exe") -Force
Copy-Item -LiteralPath $readme -Destination (Join-Path $portableDir "README.md") -Force
Copy-Item -LiteralPath $uninstaller -Destination (Join-Path $portableDir "uninstall.ps1") -Force

$launcher = @'
@echo off
start "" "%~dp0US-AI.exe"
'@
Set-Content -LiteralPath (Join-Path $portableDir "Launch US AI.cmd") -Value $launcher -Encoding ASCII

$localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
$tempBuildDir = Join-Path (Join-Path $localAppData "Temp") ("us-ai-setup-" + [guid]::NewGuid().ToString("N"))
$payloadDir = Join-Path $tempBuildDir "payload"
$sedPath = Join-Path $tempBuildDir "US-AI-Setup.sed"
$setupExe = Join-Path $outputPath "setup.exe"
$packageCreated = $false

try {
    New-Item -ItemType Directory -Path $payloadDir -Force | Out-Null
    Copy-Item -LiteralPath $buildExe -Destination (Join-Path $payloadDir "US-AI.exe")
    Copy-Item -LiteralPath $readme -Destination (Join-Path $payloadDir "README.md")
    Copy-Item -LiteralPath $uninstaller -Destination (Join-Path $payloadDir "uninstall.ps1")

    $setupScript = @'
@echo off
    powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -STA -ExecutionPolicy Bypass -File "%~dp0setup_install.ps1"
exit /b %ERRORLEVEL%
'@
    Set-Content -LiteralPath (Join-Path $payloadDir "setup.cmd") -Value $setupScript -Encoding ASCII

$installerScript = @'
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "Programs\US-AI")
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "US AI Setup"
$form.ClientSize = New-Object System.Drawing.Size(500, 382)
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ShowInTaskbar = $true
$form.BackColor = [System.Drawing.Color]::White

$header = New-Object System.Windows.Forms.Panel
$header.Location = New-Object System.Drawing.Point(0, 0)
$header.Size = New-Object System.Drawing.Size(500, 78)
$header.BackColor = [System.Drawing.Color]::WhiteSmoke
$form.Controls.Add($header)

$heading = New-Object System.Windows.Forms.Label
$heading.Text = "US AI Setup"
$heading.Location = New-Object System.Drawing.Point(18, 13)
$heading.Size = New-Object System.Drawing.Size(420, 28)
$heading.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$header.Controls.Add($heading)

$subheading = New-Object System.Windows.Forms.Label
$subheading.Text = "Your personal desktop assistant"
$subheading.Location = New-Object System.Drawing.Point(20, 43)
$subheading.Size = New-Object System.Drawing.Size(420, 20)
$subheading.ForeColor = [System.Drawing.Color]::DimGray
$header.Controls.Add($subheading)

$separator = New-Object System.Windows.Forms.Label
$separator.BorderStyle = [System.Windows.Forms.BorderStyle]::Fixed3D
$separator.Location = New-Object System.Drawing.Point(0, 78)
$separator.Size = New-Object System.Drawing.Size(500, 2)
$form.Controls.Add($separator)

$pages = @()
foreach ($index in 0..2) {
    $page = New-Object System.Windows.Forms.Panel
    $page.Location = New-Object System.Drawing.Point(0, 80)
    $page.Size = New-Object System.Drawing.Size(500, 255)
    $page.BackColor = [System.Drawing.Color]::White
    $form.Controls.Add($page)
    $pages += $page
}

$description = New-Object System.Windows.Forms.Label
$description.Text = "Welcome to the US AI Setup Wizard"
$description.Location = New-Object System.Drawing.Point(26, 20)
$description.Size = New-Object System.Drawing.Size(440, 28)
$description.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$pages[0].Controls.Add($description)

$welcome = New-Object System.Windows.Forms.Label
$welcome.Text = "This wizard will install US AI on your computer.`r`n`r`nUS AI provides voice interaction, local AI responses, memory, desktop controls, and a convenient system-tray companion.`r`n`r`nClick Next to choose the installation folder."
$welcome.Location = New-Object System.Drawing.Point(27, 61)
$welcome.Size = New-Object System.Drawing.Size(438, 145)
$pages[0].Controls.Add($welcome)

$locationHeading = New-Object System.Windows.Forms.Label
$locationHeading.Text = "Choose Install Location"
$locationHeading.Location = New-Object System.Drawing.Point(26, 20)
$locationHeading.Size = New-Object System.Drawing.Size(440, 28)
$locationHeading.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$pages[1].Controls.Add($locationHeading)

$locationDescription = New-Object System.Windows.Forms.Label
$locationDescription.Text = "Choose the folder in which to install US AI."
$locationDescription.Location = New-Object System.Drawing.Point(27, 52)
$locationDescription.Size = New-Object System.Drawing.Size(440, 22)
$pages[1].Controls.Add($locationDescription)

$pathBox = New-Object System.Windows.Forms.TextBox
$pathBox.Location = New-Object System.Drawing.Point(28, 112)
$pathBox.Size = New-Object System.Drawing.Size(345, 25)
$pathBox.Text = $InstallDir
$pages[1].Controls.Add($pathBox)

$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Text = "Browse..."
$browseButton.Location = New-Object System.Drawing.Point(382, 110)
$browseButton.Size = New-Object System.Drawing.Size(90, 28)
$browseButton.Add_Click({
    $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderDialog.Description = "Choose the US AI installation folder"
    $folderDialog.SelectedPath = $pathBox.Text
    if ($folderDialog.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {
        $pathBox.Text = $folderDialog.SelectedPath
    }
})
$pages[1].Controls.Add($browseButton)

$spaceLabel = New-Object System.Windows.Forms.Label
$spaceLabel.Text = "Space required: approximately 350 MB`r`nSpace available: Windows-managed"
$spaceLabel.Location = New-Object System.Drawing.Point(28, 164)
$spaceLabel.Size = New-Object System.Drawing.Size(440, 40)
$spaceLabel.ForeColor = [System.Drawing.Color]::DimGray
$pages[1].Controls.Add($spaceLabel)

$installHeading = New-Object System.Windows.Forms.Label
$installHeading.Text = "Installing US AI"
$installHeading.Location = New-Object System.Drawing.Point(26, 20)
$installHeading.Size = New-Object System.Drawing.Size(440, 28)
$installHeading.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$pages[2].Controls.Add($installHeading)

$status = New-Object System.Windows.Forms.Label
$status.Text = "Please wait while US AI is being installed."
$status.Location = New-Object System.Drawing.Point(27, 56)
$status.Size = New-Object System.Drawing.Size(445, 22)
$pages[2].Controls.Add($status)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Location = New-Object System.Drawing.Point(27, 94)
$progress.Size = New-Object System.Drawing.Size(445, 12)
$progress.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$progress.Minimum = 0
$progress.Maximum = 100
$progress.Value = 0
$pages[2].Controls.Add($progress)

$finishHeading = New-Object System.Windows.Forms.Label
$finishHeading.Text = "Completing US AI Setup"
$finishHeading.Location = New-Object System.Drawing.Point(26, 20)
$finishHeading.Size = New-Object System.Drawing.Size(440, 28)
$finishHeading.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$pages[2].Controls.Add($finishHeading)

$finishText = New-Object System.Windows.Forms.Label
$finishText.Text = "US AI has been installed on your computer.`r`n`r`nClick Finish to close Setup."
$finishText.Location = New-Object System.Drawing.Point(27, 56)
$finishText.Size = New-Object System.Drawing.Size(445, 54)
$finishText.Visible = $false
$pages[2].Controls.Add($finishText)

$runCheck = New-Object System.Windows.Forms.CheckBox
$runCheck.Text = "Run US AI"
$runCheck.Location = New-Object System.Drawing.Point(27, 132)
$runCheck.Size = New-Object System.Drawing.Size(200, 25)
$runCheck.Checked = $true
$runCheck.Visible = $false
$pages[2].Controls.Add($runCheck)

$installButton = New-Object System.Windows.Forms.Button
$installButton.Text = "Next >"
$installButton.Location = New-Object System.Drawing.Point(315, 345)
$installButton.Size = New-Object System.Drawing.Size(90, 30)
$installButton.Add_Click({
    try {
        if ($pages[0].Visible) {
            $pages[0].Visible = $false
            $pages[1].Visible = $true
            $installButton.Text = "Install"
            $backButton.Enabled = $true
            return
        }
        if ($pages[1].Visible) {
            $installDir = [System.IO.Path]::GetFullPath($pathBox.Text.Trim())
            if ([string]::IsNullOrWhiteSpace($pathBox.Text)) { throw "Choose an installation folder." }
            if (Get-Process -Name "US-AI" -ErrorAction SilentlyContinue) { throw "Exit US AI from the system tray before installing the update." }
            $installMarker = Join-Path $installDir ".us-ai-install-root"
            if (Test-Path -LiteralPath $installDir) {
                $existingItems = @(Get-ChildItem -LiteralPath $installDir -Force)
                if ($existingItems.Length -gt 0 -and -not (Test-Path -LiteralPath $installMarker -PathType Leaf)) { throw "The chosen folder already contains files and is not a US AI installation." }
            }
            $pages[1].Visible = $false
            $pages[2].Visible = $true
            $installButton.Enabled = $false
            $backButton.Enabled = $false
            $cancelButton.Enabled = $false
            $progress.Value = 10
            [System.Windows.Forms.Application]::DoEvents()

            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot "US-AI.exe") -Destination (Join-Path $installDir "US-AI.exe") -Force
            $progress.Value = 65
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot "README.md") -Destination (Join-Path $installDir "README.md") -Force
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot "uninstall.ps1") -Destination (Join-Path $installDir "uninstall.ps1") -Force
            Set-Content -LiteralPath $installMarker -Value $installDir -Encoding UTF8

            $startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\US AI"
            New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
            $shell = New-Object -ComObject WScript.Shell
            $launchShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "US AI.lnk"))
            $launchShortcut.TargetPath = Join-Path $installDir "US-AI.exe"
            $launchShortcut.WorkingDirectory = $installDir
            $launchShortcut.Description = "Start the US AI desktop assistant"
            $launchShortcut.Save()
            $uninstallShortcut = $shell.CreateShortcut((Join-Path $startMenuDir "Uninstall US AI.lnk"))
            $uninstallShortcut.TargetPath = Join-Path $PSHOME "powershell.exe"
            $uninstallShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$installDir\uninstall.ps1`""
            $uninstallShortcut.WorkingDirectory = $installDir
            $uninstallShortcut.Description = "Uninstall US AI"
            $uninstallShortcut.Save()

            $uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\US-AI"
            $uninstallCommand = "`"$PSHOME\powershell.exe`" -NoProfile -ExecutionPolicy Bypass -File `"$installDir\uninstall.ps1`""
            New-Item -Path $uninstallKey -Force | Out-Null
            Set-ItemProperty -Path $uninstallKey -Name DisplayName -Value "US AI"
            Set-ItemProperty -Path $uninstallKey -Name DisplayVersion -Value "1.0.0"
            Set-ItemProperty -Path $uninstallKey -Name Publisher -Value "US AI"
            Set-ItemProperty -Path $uninstallKey -Name InstallLocation -Value $installDir
            Set-ItemProperty -Path $uninstallKey -Name UninstallString -Value $uninstallCommand
            Set-ItemProperty -Path $uninstallKey -Name NoModify -Type DWord -Value 1
            Set-ItemProperty -Path $uninstallKey -Name NoRepair -Type DWord -Value 1
            $progress.Value = 100
            $status.Text = "Installation complete."
            $installHeading.Visible = $false
            $finishHeading.Visible = $true
            $finishText.Visible = $true
            $runCheck.Visible = $true
            $installButton.Text = "Finish"
            $installButton.Enabled = $true
            $installButton.Visible = $true
            $installButton.Add_Click({ if ($runCheck.Checked) { Start-Process -FilePath (Join-Path $installDir "US-AI.exe") -WorkingDirectory $installDir } ; $form.Close() })
            $installButton.Focus()
        }
    } catch {
        $status.Text = "Installation could not be completed."
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            "US AI Setup",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
        $installButton.Enabled = $true
        $browseButton.Enabled = $true
        $pathBox.Enabled = $true
        $cancelButton.Enabled = $true
    }
})
$form.Controls.Add($installButton)

$backButton = New-Object System.Windows.Forms.Button
$backButton.Text = "< Back"
$backButton.Location = New-Object System.Drawing.Point(220, 345)
$backButton.Size = New-Object System.Drawing.Size(90, 30)
$backButton.Enabled = $false
$backButton.Add_Click({
    if ($pages[1].Visible) { $pages[1].Visible = $false; $pages[0].Visible = $true; $backButton.Enabled = $false; $installButton.Text = "Next >" }
})
$form.Controls.Add($backButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = "Cancel"
$cancelButton.Location = New-Object System.Drawing.Point(410, 345)
$cancelButton.Size = New-Object System.Drawing.Size(90, 30)
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancelButton)

$pages[1].Visible = $false
$pages[2].Visible = $false
$form.AcceptButton = $installButton
$form.CancelButton = $cancelButton
[void]$form.ShowDialog()
'@
    Set-Content -LiteralPath (Join-Path $payloadDir "setup_install.ps1") -Value $installerScript -Encoding UTF8

    $sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=1
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=
DisplayLicense=
FinishMessage=
TargetName=$setupExe
FriendlyName="US AI Setup"
AppLaunched=cmd.exe /c setup.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
FILE0="setup.cmd"
FILE1="setup_install.ps1"
FILE2="US-AI.exe"
FILE3="README.md"
FILE4="uninstall.ps1"
[SourceFiles]
SourceFiles0=$payloadDir
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
%FILE3%=
%FILE4%=
"@
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($sedPath, $sed, $utf8NoBom)

    $iexpressCommand = "$iexpress /N /Q $sedPath"
    & $env:ComSpec /c $iexpressCommand
    if ($LASTEXITCODE -ne 0) {
        throw "IExpress failed with exit code $LASTEXITCODE."
    }
    if (-not (Test-Path -LiteralPath $setupExe -PathType Leaf)) {
        throw "IExpress completed without creating setup.exe."
    }

    $packageCreated = $true
    Write-Host "Windows installer created: $setupExe"
    Write-Host "Portable bundle created: $portableDir"
}
finally {
    if ($packageCreated -and (Test-Path -LiteralPath $tempBuildDir)) {
        Remove-Item -LiteralPath $tempBuildDir -Recurse -Force
    } elseif (Test-Path -LiteralPath $tempBuildDir) {
        Write-Warning "Installer build staging was preserved for diagnosis: $tempBuildDir"
    }
}
