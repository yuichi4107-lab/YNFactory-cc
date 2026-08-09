#!/bin/bash
set -euo pipefail

ROOT_DIR="${YNFACTORY_ROOT:-/Users/yuichi/YNFactory-cc}"
INPUTS_DIR="${YNFACTORY_INPUTS_DIR:-$ROOT_DIR/04_インプット/inputs}"
PYTHON="${YNFACTORY_PYTHON:-$ROOT_DIR/biz_idea_generator/.venv/bin/python3.12}"
LOG_DIR="$INPUTS_DIR/logs"
LOCAL_LOG_DIR="/Users/yuichi/Library/Logs/yn-limitless-sync"
SYNC_TIMEOUT_SECONDS="${SYNC_TIMEOUT_SECONDS:-300}"
EXTRACT_TIMEOUT_SECONDS="${EXTRACT_TIMEOUT_SECONDS:-180}"
ORGANIZE_TIMEOUT_SECONDS="${ORGANIZE_TIMEOUT_SECONDS:-120}"
ZOOM_SYNC_TIMEOUT_SECONDS="${ZOOM_SYNC_TIMEOUT_SECONDS:-300}"
ORGANIZE_ZOOM_TIMEOUT_SECONDS="${ORGANIZE_ZOOM_TIMEOUT_SECONDS:-120}"
DRIVE_INBOX_TIMEOUT_SECONDS="${DRIVE_INBOX_TIMEOUT_SECONDS:-120}"
GOOGLE_MEET_SYNC_TIMEOUT_SECONDS="${GOOGLE_MEET_SYNC_TIMEOUT_SECONDS:-120}"
ORGANIZE_GOOGLE_MEET_TIMEOUT_SECONDS="${ORGANIZE_GOOGLE_MEET_TIMEOUT_SECONDS:-120}"
PROCESS_DAILY_INPUTS_TIMEOUT_SECONDS="${PROCESS_DAILY_INPUTS_TIMEOUT_SECONDS:-120}"
mkdir -p "$LOCAL_LOG_DIR"
mkdir -p "$LOG_DIR" 2>/dev/null || true

if [ ! -x "$PYTHON" ]; then
  PYTHON="$ROOT_DIR/biz_idea_generator/.venv/bin/python"
fi

if [ ! -x "$PYTHON" ]; then
  PYTHON="/opt/homebrew/bin/python3.12"
fi

if [ ! -x "$PYTHON" ]; then
  PYTHON="/usr/bin/python3"
fi

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d)
LOG="$LOCAL_LOG_DIR/run_${TODAY}.log"

echo "=== $(date) START ===" >> "$LOG"

cd "$INPUTS_DIR"

run_with_timeout() {
  local timeout_seconds="$1"
  shift

  "$@" &
  local cmd_pid=$!

  (
    sleep "$timeout_seconds"
    if kill -0 "$cmd_pid" 2>/dev/null; then
      echo "TIMEOUT after ${timeout_seconds}s: $*"
      kill "$cmd_pid" 2>/dev/null || true
      sleep 2
      kill -9 "$cmd_pid" 2>/dev/null || true
    fi
  ) &
  local timer_pid=$!

  set +e
  wait "$cmd_pid"
  local status=$?
  set -e

  kill "$timer_pid" 2>/dev/null || true
  wait "$timer_pid" 2>/dev/null || true
  return "$status"
}

echo "--- sync_limitless.py ---" >> "$LOG"
run_with_timeout "$SYNC_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u sync_limitless.py >> "$LOG" 2>&1 || {
  echo "sync_limitless.py FAILED" >> "$LOG"
  exit 1
}

echo "--- extract_insights.py ---" >> "$LOG"
if ! run_with_timeout "$EXTRACT_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 GEMINI_TIMEOUT_SECONDS="$EXTRACT_TIMEOUT_SECONDS" "$PYTHON" -u extract_insights.py >> "$LOG" 2>&1; then
  echo "extract_insights.py WARNING: extraction failed or timed out; raw lifelog sync is preserved" >> "$LOG"
else
  echo "extract_insights.py OK" >> "$LOG"
fi

echo "--- organize_inputs.py ---" >> "$LOG"
if ! run_with_timeout "$ORGANIZE_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u organize_inputs.py >> "$LOG" 2>&1; then
  echo "organize_inputs.py WARNING: organization failed or timed out; raw and extracted files are preserved" >> "$LOG"
else
  echo "organize_inputs.py OK" >> "$LOG"
fi

echo "--- sync_zoom.py ---" >> "$LOG"
if ! run_with_timeout "$ZOOM_SYNC_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u sync_zoom.py >> "$LOG" 2>&1; then
  echo "sync_zoom.py WARNING: Zoom sync failed or timed out; existing Zoom raw files are preserved" >> "$LOG"
else
  echo "sync_zoom.py OK" >> "$LOG"
fi

echo "--- organize_zoom_inputs.py ---" >> "$LOG"
if ! run_with_timeout "$ORGANIZE_ZOOM_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u organize_zoom_inputs.py --all --force >> "$LOG" 2>&1; then
  echo "organize_zoom_inputs.py WARNING: Zoom organization failed or timed out; raw Zoom files are preserved" >> "$LOG"
else
  echo "organize_zoom_inputs.py OK" >> "$LOG"
fi

echo "--- import_drive_inbox.py ---" >> "$LOG"
if ! run_with_timeout "$DRIVE_INBOX_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u import_drive_inbox.py >> "$LOG" 2>&1; then
  echo "import_drive_inbox.py WARNING: Drive inbox import failed or timed out; source files are preserved" >> "$LOG"
else
  echo "import_drive_inbox.py OK" >> "$LOG"
fi

echo "--- sync_google_meet.py ---" >> "$LOG"
if ! run_with_timeout "$GOOGLE_MEET_SYNC_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u sync_google_meet.py >> "$LOG" 2>&1; then
  echo "sync_google_meet.py WARNING: Google Meet sync failed or timed out; source files are preserved" >> "$LOG"
else
  echo "sync_google_meet.py OK" >> "$LOG"
fi

echo "--- organize_google_meet_inputs.py ---" >> "$LOG"
if ! run_with_timeout "$ORGANIZE_GOOGLE_MEET_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u organize_google_meet_inputs.py --all --force >> "$LOG" 2>&1; then
  echo "organize_google_meet_inputs.py WARNING: Google Meet organization failed or timed out; raw files are preserved" >> "$LOG"
else
  echo "organize_google_meet_inputs.py OK" >> "$LOG"
fi

if [ -f "conversations/${YESTERDAY}-lifelogs.md" ]; then
  echo "conversation file present: conversations/${YESTERDAY}-lifelogs.md" >> "$LOG"
else
  echo "WARNING: expected conversation file missing: conversations/${YESTERDAY}-lifelogs.md" >> "$LOG"
fi

echo "--- process_daily_inputs.py ---" >> "$LOG"
if ! run_with_timeout "$PROCESS_DAILY_INPUTS_TIMEOUT_SECONDS" env PYTHONUNBUFFERED=1 "$PYTHON" -u process_daily_inputs.py --skip-refresh --force >> "$LOG" 2>&1; then
  echo "process_daily_inputs.py WARNING: daily input review failed or timed out; indexes and raw files are preserved" >> "$LOG"
else
  echo "process_daily_inputs.py OK" >> "$LOG"
fi

echo "=== $(date) DONE ===" >> "$LOG"
