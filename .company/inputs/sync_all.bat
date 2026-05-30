@echo off
cd /d "G:\マイドライブ\YNFactory-cc"
echo [%date% %time%] Starting daily inputs sync...
echo === Limitless AI ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\sync_limitless.py" --chats
echo === Zoom ===
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 ".company\inputs\sync_zoom.py"
echo [%date% %time%] Done.
