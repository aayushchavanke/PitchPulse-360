@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Desktop_Launcher.ps1"
if errorlevel 1 pause
endlocal
