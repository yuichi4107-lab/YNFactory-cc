@echo off
setlocal
cd /d "%~dp0"

if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "sync_notion.py" %*
) else (
  py -3 "sync_notion.py" %*
)
