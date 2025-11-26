#!/usr/bin/env bash
set -euo pipefail

# Start backend API server and worker with simple pid files.
# Usage: ./start_services.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}"
SERVER_PID_FILE="${ROOT_DIR}/server.pid"
WORKER_PID_FILE="${ROOT_DIR}/worker.pid"

ensure_not_running() {
  local pid_file="$1"
  local name="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" && -d "/proc/$pid" ]]; then
      echo "$name already running with PID $pid (pid file: $pid_file)"
      exit 1
    fi
  fi
}

start_process() {
  local script="$1"
  local pid_file="$2"
  local log_file="$3"
  nohup python3 "$script" > "$log_file" 2>&1 &
  echo $! > "$pid_file"
  echo "Started $(basename "$script") (pid: $(cat "$pid_file")), log: $log_file"
}

cd "$ROOT_DIR"

ensure_not_running "$SERVER_PID_FILE" "Server"
ensure_not_running "$WORKER_PID_FILE" "Worker"

start_process "$ROOT_DIR/app.py" "$SERVER_PID_FILE" "$LOG_DIR/server.log"
start_process "$ROOT_DIR/worker.py" "$WORKER_PID_FILE" "$LOG_DIR/worker.log"

echo "All services started."
