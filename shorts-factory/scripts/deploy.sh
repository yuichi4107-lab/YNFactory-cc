#!/usr/bin/env bash
# shorts-factory のセットアップ/デプロイ。
#   ./deploy.sh          コードを ~/shorts-factory/app へ同期
#   ./deploy.sh install  launchd 3ジョブの登録まで実行
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/shorts_env.sh"

DRIVE_ROOT="$(shorts_resolve_repo_root)"
SRC="$DRIVE_ROOT/shorts-factory"
APP_DIR="$HOME/shorts-factory/app"
LA_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude '.venv' --exclude 'work' --exclude 'logs' --exclude 'voicevox*' \
  "$SRC/src" "$SRC/prompts" "$SRC/assets" "$SRC/scripts" "$APP_DIR/"
chmod +x "$APP_DIR"/scripts/*.sh
echo "✅ コード同期: $APP_DIR (repo=$DRIVE_ROOT)"

if [ "${1:-}" = "install" ]; then
  for p in shorts-generate shorts-approval shorts-chrome; do
    cp "$SRC/launchd/com.ynfactory.$p.plist" "$LA_DIR/"
    launchctl unload "$LA_DIR/com.ynfactory.$p.plist" 2>/dev/null || true
    launchctl load "$LA_DIR/com.ynfactory.$p.plist"
    echo "✅ launchd登録: com.ynfactory.$p"
  done
  echo "確認: launchctl list | grep ynfactory.shorts"
fi
