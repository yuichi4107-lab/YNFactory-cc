#!/usr/bin/env bash
# 日次の動画生成エントリポイント（launchd com.ynfactory.shorts-generate から呼ばれる）。
# Driveの正本を ~/shorts-factory/app へ同期してから実行する（コード更新の自動反映）。
set -uo pipefail

DRIVE_ROOT="/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
APP_DIR="$HOME/shorts-factory/app"
VENV_PY="$HOME/shorts-factory/.venv/bin/python"

# Driveがマウントされていれば最新コードを同期（失敗しても手元コードで続行）
if [ -d "$DRIVE_ROOT/shorts-factory/src" ]; then
  mkdir -p "$APP_DIR"
  rsync -a --delete \
    --exclude '.venv' --exclude 'work' --exclude 'logs' \
    "$DRIVE_ROOT/shorts-factory/src" \
    "$DRIVE_ROOT/shorts-factory/prompts" \
    "$DRIVE_ROOT/shorts-factory/assets" \
    "$DRIVE_ROOT/shorts-factory/scripts" \
    "$APP_DIR/" 2>/dev/null || echo "[warn] rsync失敗。既存コードで続行"
fi

cd "$APP_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$VENV_PY" -m src.pipeline
