#!/usr/bin/env bash
# TikTok初回ログイン用（可視Chromeを専用プロファイルで開く）。
# 手順:
#   1. launchctl unload ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist 2>/dev/null
#   2. ./login_tiktok.sh   ← Chromeが開くので TikTok ログイン
#   3. Chromeを閉じて launchctl load ~/Library/LaunchAgents/com.ynfactory.shorts-chrome.plist
set -euo pipefail
export SHORTS_HEADLESS=0
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Chromeが開きます。TikTokにログインし、アップロード画面が見えれば完了です。"
exec "$DIR/start_chrome_shorts.sh" "https://www.tiktok.com/tiktokstudio/upload?from=upload"
