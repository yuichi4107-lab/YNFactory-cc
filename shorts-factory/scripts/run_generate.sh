#!/usr/bin/env bash
# 日次の動画生成エントリポイント（launchd com.ynfactory.shorts-generate から呼ばれる）。
# Driveの正本を ~/shorts-factory/app へ同期してから実行する（コード更新の自動反映）。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/shorts_env.sh"

if [ -d "$HOME/.nvm/versions/node" ]; then
  NODE_BIN="$(find "$HOME/.nvm/versions/node" -maxdepth 2 -type d -name bin 2>/dev/null | sort -V | tail -1)"
  if [ -n "$NODE_BIN" ]; then
    export PATH="$NODE_BIN:$PATH"
  fi
fi

APP_DIR="$HOME/shorts-factory/app"
VENV_PY="$HOME/shorts-factory/.venv/bin/python"
DRIVE_ROOT="$(shorts_resolve_repo_root || true)"

# Driveがロックされる場合に備え、コード同期だけはローカルGitミラーへフォールバックする。
CODE_ROOTS=()
shorts_add_code_root() {
  local root="${1:-}"
  [ -n "$root" ] || return 0
  [ -d "$root/shorts-factory/src" ] || return 0
  local existing
  for existing in "${CODE_ROOTS[@]+"${CODE_ROOTS[@]}"}"; do
    [ "$existing" = "$root" ] && return 0
  done
  CODE_ROOTS+=("$root")
}

shorts_add_code_root "${SHORTS_CODE_ROOT:-}"
shorts_add_code_root "$DRIVE_ROOT"
shorts_add_code_root "$HOME/YNFactory-cc"

SYNC_OK=0
if [ "${#CODE_ROOTS[@]}" -gt 0 ]; then
  for CODE_ROOT in "${CODE_ROOTS[@]}"; do
    if shorts_sync_app_from_repo "$CODE_ROOT" "$APP_DIR"; then
      echo "[info] コード同期: $CODE_ROOT -> $APP_DIR"
      SYNC_OK=1
      break
    fi
    echo "[warn] コード同期に失敗: $CODE_ROOT"
  done
fi
if [ "$SYNC_OK" -ne 1 ]; then
  echo "[warn] コード同期に失敗。既存コードで続行"
fi

cd "$APP_DIR"
if [ -n "$DRIVE_ROOT" ]; then
  export SHORTS_REPO_ROOT="$DRIVE_ROOT"
fi
export SHORTS_FACTORY_ROOT="$APP_DIR"
export PYTHONDONTWRITEBYTECODE=1
exec "$VENV_PY" -m src.pipeline "$@"
