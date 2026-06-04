#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR"
PID_FILE="$BACKEND_DIR/.uvicorn.pid"
LOG_FILE="$BACKEND_DIR/backend.log"

cd "$BACKEND_DIR"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE")"
  if kill -0 "$OLD_PID" >/dev/null 2>&1; then
    echo "Backend already running (PID: $OLD_PID)"
    exit 0
  fi
fi

nohup uvicorn app.main:app --host 127.0.0.1 --port 8001 >"$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

echo "Backend started. PID=$NEW_PID"
echo "Log file: $LOG_FILE"
