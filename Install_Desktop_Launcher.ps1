$ErrorActionPreference = 'Stop'
$desktopPath = [Environment]::GetFolderPath('Desktop')
if (!$desktopPath -or !(Test-Path -LiteralPath $desktopPath)) { throw 'The Windows Desktop folder could not be located.' }
if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Start_Football_Platform.ps1'))) { throw 'Keep this installer inside the extracted football project folder.' }
$launcherPath = Join-Path $desktopPath 'Start PitchPulse360 Football.cmd'
$content = @"
@echo off
setlocal
title PitchPulse360 Football Analytics Startup
set "PROJECT=$PSScriptRoot"
if not exist "%PROJECT%\Start_Football_Platform.ps1" (
  echo Project launcher not found at:
  echo %PROJECT%
  echo.
  echo If you moved the project, run Install_Desktop_Launcher.ps1 from its new folder.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT%\Start_Football_Platform.ps1" %*
if errorlevel 1 pause
endlocal
"@
Set-Content -LiteralPath $launcherPath -Value $content -Encoding ASCII
Write-Host "Desktop launcher created: $launcherPath" -ForegroundColor Green
