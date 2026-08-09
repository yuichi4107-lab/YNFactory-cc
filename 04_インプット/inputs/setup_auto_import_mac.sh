#!/bin/bash
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.ynfactory.inputs-auto-import.plist"
RUNNER="$HOME/scripts/run_inputs_auto_import.sh"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUTS_DIR="$ROOT_DIR/04_インプット/inputs"
PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12"
LOG_DIR="$HOME/Library/Logs/ynfactory-inputs"

if [ ! -x "$PYTHON" ]; then
  PYTHON="/usr/bin/python3"
fi

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PLIST")"
mkdir -p "$(dirname "$RUNNER")"

cat > "$RUNNER" <<EOF
#!/bin/bash
set -euo pipefail

INPUTS_DIR="$INPUTS_DIR"
PYTHON="$PYTHON"

if [ ! -x "\$PYTHON" ]; then
  PYTHON="/usr/bin/python3"
fi

cd "\$INPUTS_DIR"

echo "=== \$(date) START inputs auto import ==="

echo "--- import_drive_inbox.py ---"
"\$PYTHON" -u import_drive_inbox.py

echo "--- sync_google_meet.py ---"
"\$PYTHON" -u sync_google_meet.py

echo "--- organize_google_meet_inputs.py ---"
"\$PYTHON" -u organize_google_meet_inputs.py --all --force

echo "=== \$(date) DONE inputs auto import ==="
EOF

chmod +x "$RUNNER"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ynfactory.inputs-auto-import</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$RUNNER</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/inputs-auto-import.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/inputs-auto-import.err.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null || launchctl load "$PLIST"
launchctl kickstart -k "gui/$(id -u)/com.ynfactory.inputs-auto-import" 2>/dev/null || true

echo "Registered: $PLIST"
echo "Runner: $RUNNER"
echo "Logs: $LOG_DIR"
