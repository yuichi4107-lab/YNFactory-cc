#!/bin/bash
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.ynfactory.inputs-auto-import.plist"

launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"

echo "Removed: $PLIST"
