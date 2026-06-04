@echo off
setlocal
cd /d "%~dp0"

if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "auto_import_loop.py" --interval 300
) else (
  py -3 "auto_import_loop.py" --interval 300
)
