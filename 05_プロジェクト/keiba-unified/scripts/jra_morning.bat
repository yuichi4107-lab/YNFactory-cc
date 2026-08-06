@echo off
REM JRA中央競馬 朝予想（土日7:00）
cd /d "G:\マイドライブ\YNFactory-cc\05_プロジェクト\keiba-unified\jra"
python "G:\マイドライブ\YNFactory-cc\05_プロジェクト\keiba-unified\jra\scripts\run_morning.py" >> "G:\マイドライブ\YNFactory-cc\05_プロジェクト\keiba-unified\jra\data\reports\morning.log" 2>&1
