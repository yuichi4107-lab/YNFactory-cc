@echo off
cd /d "%~dp0"
chcp 65001 >nul
set "PATH=%APPDATA%\npm;%PATH%"

if exist ".venv\Scripts\python.exe" goto use_venv

where py >nul 2>nul
if errorlevel 1 goto use_python

cmd.exe /k py -3 main.py --voice
exit /b

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
cmd.exe /k python main.py --voice
exit /b

:use_venv
cmd.exe /k ".venv\Scripts\python.exe" main.py --voice
exit /b

:no_python
echo Python was not found. Install Python 3.11 or later.
pause
