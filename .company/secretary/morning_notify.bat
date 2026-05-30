@echo off
REM === 朝のTODO通知 ===
REM タスクスケジューラから毎朝6:30に実行

cd /d "%~dp0"
python morning_notify.py >> morning_notify.log 2>&1
