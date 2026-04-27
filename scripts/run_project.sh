#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PID_DIR="$SCRIPT_DIR/.pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

BACKEND_PORT="${BACKEND_PORT:-5000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

mkdir -p "$PID_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but not found."
  exit 1
fi

if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
  echo "Backend appears to already be running (PID $(cat "$BACKEND_PID_FILE"))."
  echo "Run scripts/stop_project.sh first, or remove stale PID files in scripts/.pids."
  exit 1
fi

if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
  echo "Frontend appears to already be running (PID $(cat "$FRONTEND_PID_FILE"))."
  echo "Run scripts/stop_project.sh first, or remove stale PID files in scripts/.pids."
  exit 1
fi

cleanup() {
  echo
  echo "Shutting down services..."

  if [[ -n "${FRONTEND_PID:-}" ]]; then
    pkill -TERM -P "$FRONTEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "${BACKEND_PID:-}" ]]; then
    pkill -TERM -P "$BACKEND_PID" 2>/dev/null || true
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

(
  cd "$BACKEND_DIR"

  if [[ -x ".venv/bin/python" ]]; then
    echo "[backend] starting with backend/.venv"
    .venv/bin/python -m flask --app app run --port "$BACKEND_PORT"
  else
    echo "[backend] starting with system python3"
    python3 -m flask --app app run --port "$BACKEND_PORT"
  fi
) &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"

(
  cd "$FRONTEND_DIR"
  echo "[frontend] starting Vite dev server"
  VITE_BACKEND_TARGET="http://127.0.0.1:${BACKEND_PORT}" \
    npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"

echo ""
echo "Backend:  http://127.0.0.1:${BACKEND_PORT}"
echo "Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "Press Ctrl+C to stop both."
echo ""

while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend process exited."
    exit 1
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "Frontend process exited."
    exit 1
  fi

  sleep 1
done
