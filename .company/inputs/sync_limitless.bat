@echo off
setlocal
set "ROOT=C:\YNFactory-cc"
set "PY=%ROOT%\biz_idea_generator\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe"
cd /d "%ROOT%"
"%PY%" -X utf8 ".company\inputs\sync_limitless.py" --chats
