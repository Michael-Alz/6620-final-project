#!/usr/bin/env bash
set -euo pipefail

# Stop backend API server and all workers using pid files.
# Usage: ./stop_services.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PID_FILE="${ROOT_DIR}/server.pid"

stop_process() {
  local pid_file="$1"
  local name="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "$name not running (no pid file: $pid_file)"
    return
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    echo "$name pid file empty, removing: $pid_file"
    rm -f "$pid_file"
    return
  fi

  if [[ ! -d "/proc/$pid" ]]; then
    echo "$name pid $pid not found, removing stale pid file: $pid_file"
    rm -f "$pid_file"
    return
  fi

  echo "Stopping $name (pid: $pid)"
  kill "$pid" || true
  # Give it a moment to exit gracefully.
  sleep 1
  if [[ -d "/proc/$pid" ]]; then
    echo "$name still running, sending SIGKILL"
    kill -9 "$pid" || true
  fi
  rm -f "$pid_file"
  echo "$name stopped."
}

stop_process "$SERVER_PID_FILE" "Server"
# stop all worker pid files (worker_*.pid)
for pid_file in "$ROOT_DIR"/worker_*.pid; do
  if [[ -e "$pid_file" ]]; then
    worker_name="$(basename "$pid_file" .pid)"
    stop_process "$pid_file" "$worker_name"
  fi
done

echo "All stop commands issued."
