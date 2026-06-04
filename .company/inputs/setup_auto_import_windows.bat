@echo off
setlocal

set "TASK_NAME=YNFactory Inputs Auto Import"
set "SCRIPT=%~dp0auto_import_windows.bat"

echo Registering scheduled task: %TASK_NAME%
echo Script: %SCRIPT%

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%SCRIPT%\"" ^
  /SC MINUTE ^
  /MO 5 ^
  /F

if errorlevel 1 (
  echo Failed to register scheduled task.
  echo Try running this file as Administrator, or use setup_auto_import_windows_logon.bat.
  pause
  exit /b 1
)

echo Scheduled task registered.
echo It will run every 5 minutes while Windows is available.
pause
