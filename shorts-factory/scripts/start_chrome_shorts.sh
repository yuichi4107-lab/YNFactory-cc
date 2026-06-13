#!/usr/bin/env bash
# shorts-factory用 常駐Chrome起動（専用プロファイル + remote-debugging port 9223）。
# launchd(com.ynfactory.shorts-chrome) から KeepAlive で常時起動される。
# youtube_cdp.py / tiktok_cdp.py はこのChromeへCDP接続して投稿する。
#
# notebooklm-sync の start_chrome_mac.sh と同パターン（ポートとプロファイルのみ別）。
#
# 環境変数:
#   SHORTS_AUTH_DIR   プロファイル（既定: ~/shorts-factory/.auth/chrome）
#   SHORTS_CDP_PORT   remote-debuggingポート（既定: 9223）
#   SHORTS_HEADLESS   1ならheadless(--headless=new) / 0なら通常ウィンドウ（既定: 0）
set -euo pipefail

PROFILE="${SHORTS_AUTH_DIR:-$HOME/shorts-factory/.auth/chrome}"
PORT="${SHORTS_CDP_PORT:-9223}"
HEADLESS="${SHORTS_HEADLESS:-0}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

mkdir -p "$PROFILE"

ARGS=(
  --user-data-dir="$PROFILE"
  --remote-debugging-port="$PORT"
  --no-first-run
  --no-default-browser-check
  --window-size=1400,1000
  --disable-features=Translate
  --disable-background-timer-throttling
  --disable-backgrounding-occluded-windows
)
if [ "$HEADLESS" = "1" ]; then
  ARGS+=(--headless=new)
fi

exec "$CHROME" "${ARGS[@]}" about:blank
