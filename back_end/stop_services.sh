#!/usr/bin/env bash
set -euo pipefail

# Stop backend API server and worker using pid files.
# Usage: ./stop_services.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PID_FILE="${ROOT_DIR}/server.pid"
WORKER_PID_FILE="${ROOT_DIR}/worker.pid"

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
stop_process "$WORKER_PID_FILE" "Worker"

echo "All stop commands issued."
