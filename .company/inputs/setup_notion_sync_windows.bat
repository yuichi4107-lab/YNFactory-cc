@echo off
setlocal

set "TASK_NAME=YNFactory Notion Sync"
set "SCRIPT=%~dp0notion_sync.bat"

echo Registering scheduled task: %TASK_NAME%
echo Script: %SCRIPT%

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%SCRIPT%\"" ^
  /SC DAILY ^
  /ST 07:30 ^
  /F

if errorlevel 1 (
  echo Failed to register scheduled task.
  echo Try running this file as Administrator.
  pause
  exit /b 1
)

echo Scheduled task registered.
echo It will run daily at 07:30.
pause
