@echo off
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" goto no_venv
".venv\Scripts\python.exe" -m ai_planner.voice_setup --list-devices
goto end

:no_venv
echo Run the speech recognition setup file first.

:end
echo.
pause
