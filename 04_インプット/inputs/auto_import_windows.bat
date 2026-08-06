@echo off
setlocal
cd /d "%~dp0"

if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "import_drive_inbox.py"
) else (
  py -3 "import_drive_inbox.py"
)
