#!/usr/bin/env bash
set -euo pipefail

# Start backend API server (gunicorn, multi-threaded) and multiple workers.
# Usage: ./start_services.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}"
SERVER_PID_FILE="${ROOT_DIR}/server.pid"

# Defaults: API uses 3 workers / 4 threads; queue workers default to 2 (override via envs).
API_WORKERS="${API_WORKERS:-3}"
API_THREADS="${API_THREADS:-4}"
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
  local cmd="$1"
  local pid_file="$2"
  local log_file="$3"
  local name="$4"

  if ! ensure_not_running "$pid_file" "$name"; then
    return
  fi
  nohup bash -c "$cmd" > "$log_file" 2>&1 &
  echo $! > "$pid_file"
  echo "Started $name (pid: $(cat "$pid_file")), log: $log_file"
}

cd "$ROOT_DIR"

# Start API server via gunicorn (multi-threaded).
SERVER_CMD="cd \"$ROOT_DIR\" && gunicorn --workers \"$API_WORKERS\" --threads \"$API_THREADS\" --bind 0.0.0.0:8080 run:app"
start_process "$SERVER_CMD" "$SERVER_PID_FILE" "$LOG_DIR/server.log" "server"

echo "Starting $WORKER_COUNT workers..."
for i in $(seq 1 "$WORKER_COUNT"); do
  worker_pid_file="${ROOT_DIR}/worker_${i}.pid"
  worker_log_file="${LOG_DIR}/worker_${i}.log"
  WORKER_CMD="cd \"$ROOT_DIR\" && python3 \"$ROOT_DIR/worker.py\""
  start_process "$WORKER_CMD" "$worker_pid_file" "$worker_log_file" "worker_$i"
done

echo "All services started."
