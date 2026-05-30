@echo off
REM === タスクスケジューラ登録スクリプト ===
REM 管理者権限で実行してください

echo タスクスケジューラに「朝のTODO通知」を登録します...

schtasks /create ^
  /tn "YNFactory\MorningTodo" ^
  /tr "\"%~dp0morning_notify.bat\"" ^
  /sc daily ^
  /st 06:30 ^
  /rl HIGHEST ^
  /f

if %errorlevel% neq 0 (
    echo.
    echo *** 登録に失敗しました。管理者権限で再実行してください。 ***
    echo     右クリック → 「管理者として実行」
) else (
    echo.
    echo 登録完了！ 毎朝 6:30 に TODO通知が送信されます。
    echo.
    echo タスク名: YNFactory\MorningTodo
    echo 確認:     schtasks /query /tn "YNFactory\MorningTodo"
    echo 削除:     schtasks /delete /tn "YNFactory\MorningTodo" /f
)

pause
