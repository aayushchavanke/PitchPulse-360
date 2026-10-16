@echo off
setlocal
title PitchPulse360 Football Analytics
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_Football_Platform.ps1" %*
if errorlevel 1 pause
endlocal
