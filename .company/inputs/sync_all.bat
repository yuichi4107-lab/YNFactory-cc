@echo off
cd /d "G:\マイドライブ\YNFactory-cc"
echo [%date% %time%] Starting daily inputs sync...
echo === Limitless AI ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\sync_limitless.py" --chats
echo === Limitless AI Insights ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\extract_insights.py"
echo === Organize Limitless Inputs ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\organize_inputs.py"
echo === Zoom ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\sync_zoom.py"
echo === Organize Zoom Inputs ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\organize_zoom_inputs.py" --all --force
echo === Import Google Drive Input Box ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\import_drive_inbox.py"
echo === Google Meet ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\sync_google_meet.py"
echo === Organize Google Meet Inputs ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\organize_google_meet_inputs.py" --all --force
echo [%date% %time%] Done.
