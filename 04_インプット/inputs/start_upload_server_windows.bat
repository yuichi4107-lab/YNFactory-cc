@echo off
setlocal
cd /d "%~dp0"

if exist "..\..\biz_idea_generator\.venv\Scripts\python.exe" (
  "..\..\biz_idea_generator\.venv\Scripts\python.exe" "upload_server.py" --host 0.0.0.0 --port 8787
) else (
  py -3 "upload_server.py" --host 0.0.0.0 --port 8787
)

pause
