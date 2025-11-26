#!/usr/bin/env bash
set -euo pipefail

# Start backend API server and multiple workers with simple pid files.
# Usage: ./start_services.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}"
SERVER_PID_FILE="${ROOT_DIR}/server.pid"
# Default worker count (override via WORKER_COUNT env)
WORKER_COUNT="${WORKER_COUNT:-2}"

ensure_not_running() {
  local pid_file="$1"
  local name="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" && -d "/proc/$pid" ]]; then
      echo "$name already running with PID $pid (pid file: $pid_file)"
      return 1
    fi
  fi
  return 0
}

start_process() {
  local script="$1"
  local pid_file="$2"
  local log_file="$3"
  if ! ensure_not_running "$pid_file" "$(basename "$script")"; then
    return
  fi
  nohup python3 "$script" > "$log_file" 2>&1 &
  echo $! > "$pid_file"
  echo "Started $(basename "$script") (pid: $(cat "$pid_file")), log: $log_file"
}

cd "$ROOT_DIR"

start_process "$ROOT_DIR/app.py" "$SERVER_PID_FILE" "$LOG_DIR/server.log"

echo "Starting $WORKER_COUNT workers..."
for i in $(seq 1 "$WORKER_COUNT"); do
  worker_pid_file="${ROOT_DIR}/worker_${i}.pid"
  worker_log_file="${LOG_DIR}/worker_${i}.log"
  start_process "$ROOT_DIR/worker.py" "$worker_pid_file" "$worker_log_file"
done

echo "All services started."
