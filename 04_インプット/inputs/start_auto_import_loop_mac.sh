#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12"

if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

cd "$SCRIPT_DIR"
"$PYTHON" auto_import_loop.py --interval "${YN_INPUT_AUTO_IMPORT_INTERVAL:-300}"
