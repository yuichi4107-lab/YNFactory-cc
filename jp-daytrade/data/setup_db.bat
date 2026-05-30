@echo off
REM =============================================================================
REM JP-DAYTRADE-v1 データ基盤セットアップ（Windows バッチ版）
REM =============================================================================
REM 用途:
REM   1. SQLite スキーマ初期化（stocks_master.db, daily_prices.db, quotes_live.db）
REM   2. J-Quants 認証確認（JQUANTS_REFRESH_TOKEN が設定済みか確認）
REM
REM 実行方法:
REM   cd jp-daytrade
REM   data\setup_db.bat
REM =============================================================================

setlocal EnableDelayedExpansion

set "DATA_DIR=%~dp0"
set "SCHEMA_DIR=%DATA_DIR%schemas"
set "CONFIG_DIR=%DATA_DIR%..\config"
set "ENV_FILE=%CONFIG_DIR%\.env"
set "ROOT_DIR=%DATA_DIR%\.."

echo.
echo =================================================
echo   JP-DAYTRADE-v1 データ基盤セットアップ (Windows)
echo =================================================
echo.

REM タイマー開始
for /f "tokens=1-3 delims=:." %%a in ("%TIME%") do (
    set /a START_SEC=%%a*3600+%%b*60+%%c
)

REM -------------------------------------------------------------------------
REM ステップ1: Python 確認
REM -------------------------------------------------------------------------
echo [1/5] 環境確認...

python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python が見つかりません。Python 3.9+ をインストールしてください。
    pause
    exit /b 1
)
echo   OK

REM -------------------------------------------------------------------------
REM ステップ2: .env ファイル確認
REM -------------------------------------------------------------------------
echo.
echo [2/5] 設定ファイル確認...

if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

if not exist "%ENV_FILE%" (
    if exist "%CONFIG_DIR%\kabu_config.env.example" (
        copy "%CONFIG_DIR%\kabu_config.env.example" "%ENV_FILE%" >nul
        echo   config\.env を作成しました（テンプレートからコピー）
    ) else (
        type nul > "%ENV_FILE%"
        echo   WARNING: 空の config\.env を作成しました
    )
) else (
    echo   config\.env: 存在します
)

REM .env から JQUANTS_REFRESH_TOKEN を読み込み
set JQUANTS_REFRESH_TOKEN=
for /f "tokens=1,2 delims==" %%a in (%ENV_FILE%) do (
    if "%%a"=="JQUANTS_REFRESH_TOKEN" set JQUANTS_REFRESH_TOKEN=%%b
)

if "%JQUANTS_REFRESH_TOKEN%"=="" (
    echo.
    echo   WARNING: JQUANTS_REFRESH_TOKEN が未設定です
    echo   設定方法: config\.env に以下を追記してください:
    echo     JQUANTS_REFRESH_TOKEN=your_refresh_token_here
    echo   登録URL: https://jpx.gitbook.io/j-quants-ja
    echo.
    echo   ※ 未設定でも DB 初期化・モック開発は継続可能です
    set JQUANTS_READY=false
) else (
    echo   JQUANTS_REFRESH_TOKEN: 設定済み
    set JQUANTS_READY=true
)

REM -------------------------------------------------------------------------
REM ステップ3: SQLite DB 初期化
REM -------------------------------------------------------------------------
echo.
echo [3/5] SQLite DB 初期化...

python -c "
import sqlite3, os

def init_db(db_path, schema_file):
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    with open(schema_file, encoding='utf-8') as f:
        sql = f.read()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.commit()
    print(f'  Initialized: {db_path}')

data_dir = r'%DATA_DIR%'
schema_dir = r'%SCHEMA_DIR%'

init_db(os.path.join(data_dir, 'stocks_master.db'), os.path.join(schema_dir, 'stocks_master.sql'))
init_db(os.path.join(data_dir, 'daily_prices.db'),  os.path.join(schema_dir, 'daily_prices.sql'))
init_db(os.path.join(data_dir, 'quotes_live.db'),   os.path.join(schema_dir, 'quotes_live.sql'))
"
if errorlevel 1 (
    echo ERROR: DB 初期化に失敗しました
    pause
    exit /b 1
)
echo   DB 初期化完了

REM -------------------------------------------------------------------------
REM ステップ4: 必要パッケージ確認
REM -------------------------------------------------------------------------
echo.
echo [4/5] 必要パッケージ確認...

if exist "%ROOT_DIR%\requirements.txt" (
    pip show requests >nul 2>&1
    if errorlevel 1 (
        echo   WARNING: 一部パッケージが未インストールです
        echo   実行してください: pip install -r requirements.txt
    ) else (
        echo   主要パッケージ確認 OK
    )
) else (
    echo   requirements.txt が見つかりません
)

REM -------------------------------------------------------------------------
REM ステップ5: 動作確認
REM -------------------------------------------------------------------------
echo.
echo [5/5] 動作確認...

python -c "
import sqlite3, sys, os

data_dir = r'%DATA_DIR%'
checks = [
    (os.path.join(data_dir, 'stocks_master.db'), 'stocks_master'),
    (os.path.join(data_dir, 'daily_prices.db'),  'daily_prices'),
    (os.path.join(data_dir, 'quotes_live.db'),   'quotes_snapshot'),
]

all_ok = True
for db_path, table in checks:
    if not os.path.exists(db_path):
        print(f'  [FAIL] {table} (DB not found)')
        all_ok = False
        continue
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',)).fetchall()
    table_names = [r[0] for r in rows]
    ok = table in table_names
    print(f'  [{\"OK\" if ok else \"FAIL\"}] {table}')
    if not ok:
        all_ok = False

if not all_ok:
    sys.exit(1)
"
if errorlevel 1 (
    echo ERROR: 動作確認に失敗しました
    pause
    exit /b 1
)

REM -------------------------------------------------------------------------
REM 完了レポート
REM -------------------------------------------------------------------------
echo.
echo =================================================
echo   セットアップ完了
echo =================================================
echo.
echo 作成ファイル:
echo   %DATA_DIR%stocks_master.db
echo   %DATA_DIR%daily_prices.db
echo   %DATA_DIR%quotes_live.db
echo.

if "%JQUANTS_READY%"=="true" (
    echo 次のステップ: J-Quants 日足データ取得
    echo   python data\jquants_client.py fetch_all_growth
) else (
    echo 次のステップ（J-Quants設定後）:
    echo   1. config\.env に JQUANTS_REFRESH_TOKEN を追記
    echo   2. python data\jquants_client.py fetch_all_growth
    echo.
    echo J-Quants設定なしで可能な作業:
    echo   - kabu API モック起動: python data\kabu_mock.py
    echo   - 気配保存テスト: python data\kabu_push_recorder.py --use-mock --no-time-window
    echo   - テスト実行: pytest tests\ -v
)
echo.

pause
