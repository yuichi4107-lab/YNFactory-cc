@echo off
setlocal

set "TASK_NAME=YNFactory Notion Sync"

echo Removing scheduled task: %TASK_NAME%

schtasks /Delete /TN "%TASK_NAME%" /F

if errorlevel 1 (
  echo Failed to remove scheduled task. It may not exist.
  pause
  exit /b 1
)

echo Scheduled task removed.
pause
