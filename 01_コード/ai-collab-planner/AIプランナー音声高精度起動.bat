@echo off
cd /d "%~dp0"
chcp 65001 >nul
set "PATH=%APPDATA%\npm;%PATH%"

if not exist ".venv\Scripts\python.exe" goto no_venv
cmd.exe /k ".venv\Scripts\python.exe" main.py --voice --whisper-model medium
exit /b

:no_venv
echo High accuracy speech recognition is not installed.
echo Run the speech recognition setup files first.
pause
