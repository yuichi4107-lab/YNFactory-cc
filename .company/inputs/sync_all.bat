@echo off
setlocal
set "ROOT=C:\YNFactory-cc"
set "PY=%ROOT%\biz_idea_generator\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe"
cd /d "%ROOT%"
echo [%date% %time%] Starting daily inputs sync...
echo === Limitless AI ===
"%PY%" -X utf8 ".company\inputs\sync_limitless.py" --chats
echo === Limitless AI Insights ===
"%PY%" -X utf8 ".company\inputs\extract_insights.py"
echo === Organize Limitless Inputs ===
"%PY%" -X utf8 ".company\inputs\organize_inputs.py"
echo === Zoom ===
"%PY%" -X utf8 ".company\inputs\sync_zoom.py"
echo === Organize Zoom Inputs ===
"%PY%" -X utf8 ".company\inputs\organize_zoom_inputs.py" --all --force
echo === Import Google Drive Input Box ===
"%PY%" -X utf8 ".company\inputs\import_drive_inbox.py"
echo === Google Meet ===
"%PY%" -X utf8 ".company\inputs\sync_google_meet.py"
echo === Organize Google Meet Inputs ===
"%PY%" -X utf8 ".company\inputs\organize_google_meet_inputs.py" --all --force
echo [%date% %time%] Done.
