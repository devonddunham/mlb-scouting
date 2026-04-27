#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

stop_from_pid_file() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    rm -f "$pid_file"
    return 1
  fi

  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (PID $pid)"
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    sleep 1
    pkill -KILL -P "$pid" 2>/dev/null || true
    kill -9 "$pid" 2>/dev/null || true
  fi

  rm -f "$pid_file"
  return 0
}

stopped_any=0

# Stop frontend first, then backend.
# Backend launcher trap may remove both PID files when it exits.
if stop_from_pid_file "frontend launcher" "$FRONTEND_PID_FILE"; then
  stopped_any=1
fi

if stop_from_pid_file "backend launcher" "$BACKEND_PID_FILE"; then
  stopped_any=1
fi

# Fallback: stop matching project-local processes if PID files are missing/stale
while IFS= read -r pid; do
  [[ -z "$pid" ]] && continue
  echo "Stopping backend process $pid"
  kill "$pid" 2>/dev/null || true
  stopped_any=1
done < <(pgrep -f "$PROJECT_ROOT/backend.*flask --app app run" || true)

while IFS= read -r pid; do
  [[ -z "$pid" ]] && continue
  echo "Stopping frontend process $pid"
  kill "$pid" 2>/dev/null || true
  stopped_any=1
done < <(pgrep -f "$PROJECT_ROOT/frontend/node_modules/.bin/vite" || true)

if [[ "$stopped_any" -eq 0 ]]; then
  echo "No matching backend/frontend processes were found."
else
  echo "Done."
fi
