@echo off
setlocal

set "TASK_NAME=YNFactory Inputs Auto Import"
set "SCRIPT=%~dp0auto_import_windows.bat"

echo Registering scheduled task at logon with 5-minute repetition: %TASK_NAME%
echo Script: %SCRIPT%

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%SCRIPT%\"" ^
  /SC ONLOGON ^
  /F

if errorlevel 1 (
  echo Failed to register scheduled task.
  pause
  exit /b 1
)

echo Scheduled task registered.
echo If you need strict 5-minute repetition, adjust the task in Windows Task Scheduler UI.
pause
