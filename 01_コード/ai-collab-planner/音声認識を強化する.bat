@echo off
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================
echo High accuracy Japanese speech recognition setup
echo ================================================
echo.
echo This creates a private Python environment in this folder.
echo The first model download can take several minutes.
echo.

where py >nul 2>nul
if errorlevel 1 goto use_python

if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed
goto install

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto failed

:install
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-voice.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m ai_planner.voice_setup
if errorlevel 1 goto failed
echo.
echo Setup completed successfully.
goto end

:no_python
echo Python was not found. Install Python 3.11 or later.
goto end

:failed
echo.
echo Setup failed. Check the messages above.

:end
echo.
pause
