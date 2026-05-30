#!/bin/bash
set -euo pipefail

INPUTS_DIR="/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/.company/inputs"
PYTHON="/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/biz_idea_generator/.venv/bin/python3.12"
LOG_DIR="$INPUTS_DIR/logs"
mkdir -p "$LOG_DIR"
TODAY=$(date +%Y-%m-%d)
LOG="$LOG_DIR/run_${TODAY}.log"

echo "=== $(date) START ===" >> "$LOG"

cd "$INPUTS_DIR"

echo "--- sync_limitless.py ---" >> "$LOG"
"$PYTHON" sync_limitless.py >> "$LOG" 2>&1 || {
  echo "sync_limitless.py FAILED" >> "$LOG"
  exit 1
}

echo "--- extract_insights.py ---" >> "$LOG"
"$PYTHON" extract_insights.py >> "$LOG" 2>&1 || {
  echo "extract_insights.py FAILED" >> "$LOG"
  exit 1
}

echo "=== $(date) DONE ===" >> "$LOG"
