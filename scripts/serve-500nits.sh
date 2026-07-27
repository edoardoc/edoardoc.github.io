#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

if ! command -v serve-nginx >/dev/null 2>&1; then
  echo "serve-nginx is not installed or is not on PATH." >&2
  exit 1
fi

pids=()

stop_servers() {
  trap - EXIT INT TERM

  for pid in "${pids[@]}"; do
    kill "${pid}" 2>/dev/null || true
  done

  for pid in "${pids[@]}"; do
    wait "${pid}" 2>/dev/null || true
  done
}

start_server() {
  local directory="$1"
  local port="$2"

  if [[ ! -d "${directory}" ]]; then
    echo "Site directory does not exist: ${directory}" >&2
    exit 1
  fi

  (
    cd "${directory}"
    PORT="${port}" exec serve-nginx
  ) &
  pids+=("$!")
}

trap stop_servers EXIT INT TERM

start_server "${ROOT}" 8080
start_server "${ROOT}/doodletag_500nits_com" 8081
start_server "${ROOT}/task_500nits_com" 8082

echo
echo "500nits sites:"
echo "  http://localhost:8080  (www.500nits.com)"
echo "  http://localhost:8081  (doodletag.500nits.com)"
echo "  http://localhost:8082  (task.500nits.com)"
echo
echo "Press Ctrl-C to stop all three servers."

wait
