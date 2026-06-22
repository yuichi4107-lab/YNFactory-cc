#!/usr/bin/env bash
# 日次の動画生成エントリポイント（launchd com.ynfactory.shorts-generate から呼ばれる）。
# Driveの正本を ~/shorts-factory/app へ同期してから実行する（コード更新の自動反映）。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/shorts_env.sh"

APP_DIR="$HOME/shorts-factory/app"
VENV_PY="$HOME/shorts-factory/.venv/bin/python"
DRIVE_ROOT="$(shorts_resolve_repo_root || true)"

# Driveがマウントされていれば最新コードを同期（失敗しても手元コードで続行）
if [ -n "$DRIVE_ROOT" ] && [ -d "$DRIVE_ROOT/shorts-factory/src" ]; then
  shorts_sync_app_from_repo "$DRIVE_ROOT" "$APP_DIR" || echo "[warn] コード同期に失敗。既存コードで続行"
else
  echo "[warn] Driveルートを解決できません。既存コードで続行"
fi

cd "$APP_DIR"
if [ -n "$DRIVE_ROOT" ]; then
  export SHORTS_REPO_ROOT="$DRIVE_ROOT"
fi
export PYTHONDONTWRITEBYTECODE=1
exec "$VENV_PY" -m src.pipeline "$@"
