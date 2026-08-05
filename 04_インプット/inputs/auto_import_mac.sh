#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12"

if [ ! -x "$PYTHON" ]; then
  PYTHON="/usr/bin/python3"
fi

cd "$SCRIPT_DIR"

echo "=== $(date) START inputs auto import ==="

echo "--- import_drive_inbox.py ---"
"$PYTHON" -u import_drive_inbox.py

echo "--- sync_google_meet.py ---"
"$PYTHON" -u sync_google_meet.py

echo "--- organize_google_meet_inputs.py ---"
"$PYTHON" -u organize_google_meet_inputs.py --all --force

echo "=== $(date) DONE inputs auto import ==="
