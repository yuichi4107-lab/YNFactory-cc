#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12"

if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

cd "$SCRIPT_DIR"
"$PYTHON" upload_server.py --host 0.0.0.0 --port "${YN_INPUT_UPLOAD_PORT:-8787}"
