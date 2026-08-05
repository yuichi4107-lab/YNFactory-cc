@echo off
setlocal

set "TASK_NAME=YNFactory Inputs Auto Import"

schtasks /Delete /TN "%TASK_NAME%" /F

if errorlevel 1 (
  echo Failed to remove scheduled task, or it was not registered.
  pause
  exit /b 1
)

echo Scheduled task removed.
pause
