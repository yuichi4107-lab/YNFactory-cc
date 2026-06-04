#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$INPUTS_DIR/../.." && pwd)"
PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12"

if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

cd "$INPUTS_DIR"
"$PYTHON" import_drive_inbox.py
