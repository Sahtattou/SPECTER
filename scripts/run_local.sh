#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${ROOT_DIR}/run"
LOG_DIR="${ROOT_DIR}/logs"

API_LOG="${LOG_DIR}/api.log"
WORKER_LOG="${LOG_DIR}/worker.log"
COLLECTOR_LOG="${LOG_DIR}/collector.log"
AGENTS_LOG="${LOG_DIR}/agents.log"
DASHBOARD_LOG="${LOG_DIR}/dashboard.log"

API_PID_FILE="${RUN_DIR}/api.pid"
WORKER_PID_FILE="${RUN_DIR}/worker.pid"
COLLECTOR_PID_FILE="${RUN_DIR}/collector.pid"
AGENTS_PID_FILE="${RUN_DIR}/agents.pid"
DASHBOARD_PID_FILE="${RUN_DIR}/dashboard.pid"

API_PORT="${API_PORT:-8080}"
AGENTS_PORT="${AGENTS_PORT:-8001}"
DASHBOARD_PORT="${DASHBOARD_PORT:-5173}"

mkdir -p "${RUN_DIR}" "${LOG_DIR}"

merge_origins() {
  local base="$1"
  shift

  local merged="${base}"
  local origin
  for origin in "$@"; do
    [[ -z "$origin" ]] && continue
    if [[ -z "$merged" ]]; then
      merged="$origin"
      continue
    fi
    case ",$merged," in
      *",${origin},"*) ;;
      *) merged="${merged},${origin}" ;;
    esac
  done

  printf '%s' "$merged"
}

is_descendant_of() {
  local pid="$1"
  local ancestor="$2"

  if [[ -z "$pid" || -z "$ancestor" ]]; then
    return 1
  fi

  while [[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 ]]; do
    if [[ "$pid" == "$ancestor" ]]; then
      return 0
    fi

    if [[ ! -r "/proc/${pid}/status" ]]; then
      return 1
    fi

    local ppid=""
    ppid="$(awk '/^PPid:/ {print $2}' "/proc/${pid}/status" 2>/dev/null || true)"

    if [[ -z "$ppid" || "$ppid" == "0" || "$ppid" == "$pid" ]]; then
      return 1
    fi

    pid="$ppid"
  done

  return 1
}

stop_orphan_processes() {
  local name="$1"
  local pattern="$2"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -z "$pids" ]]; then
    return
  fi

  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue

    local proc_cwd=""
    proc_cwd="$(readlink "/proc/${pid}/cwd" 2>/dev/null || true)"
    if [[ "$proc_cwd" != "$ROOT_DIR" ]]; then
      continue
    fi

    local tracked_pid=""
    case "$name" in
      api) [[ -f "$API_PID_FILE" ]] && tracked_pid="$(cat "$API_PID_FILE")" ;;
      worker) [[ -f "$WORKER_PID_FILE" ]] && tracked_pid="$(cat "$WORKER_PID_FILE")" ;;
      collector) [[ -f "$COLLECTOR_PID_FILE" ]] && tracked_pid="$(cat "$COLLECTOR_PID_FILE")" ;;
    esac

    if [[ -n "$tracked_pid" ]]; then
      if [[ "$pid" == "$tracked_pid" ]]; then
        continue
      fi

      if is_descendant_of "$pid" "$tracked_pid"; then
        continue
      fi
    fi

    echo "[run-local] stopping orphan ${name} process (pid ${pid})"
    kill "$pid" 2>/dev/null || true
  done <<< "$pids"
}

is_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

start_service() {
  local name="$1"
  local pid_file="$2"
  local log_file="$3"
  local command="$4"

  if is_running "$pid_file"; then
    echo "[run-local] ${name} already running (pid $(cat "$pid_file"))"
    return
  fi

  echo "[run-local] starting ${name}"
  if command -v setsid >/dev/null 2>&1; then
    setsid bash -lc "cd \"${ROOT_DIR}\" && ${command}" < /dev/null >"$log_file" 2>&1 &
  else
    nohup bash -lc "cd \"${ROOT_DIR}\" && ${command}" < /dev/null >"$log_file" 2>&1 &
  fi
  local pid=$!
  echo "$pid" > "$pid_file"
}

stop_service() {
  local name="$1"
  local pid_file="$2"

  if ! is_running "$pid_file"; then
    rm -f "$pid_file"
    echo "[run-local] ${name} not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  echo "[run-local] stopping ${name} (pid ${pid})"
  kill "$pid" 2>/dev/null || true

  local waited=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    if [[ "$waited" -gt 25 ]]; then
      echo "[run-local] force killing ${name} (pid ${pid})"
      kill -9 "$pid" 2>/dev/null || true
      break
    fi
  done

  rm -f "$pid_file"
}

wait_for_http() {
  local label="$1"
  local url="$2"
  local timeout_seconds="$3"

  local elapsed=0
  until curl -sS "$url" >/dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed + 1))
    if [[ "$elapsed" -ge "$timeout_seconds" ]]; then
      echo "[run-local] ERROR: ${label} health check failed at ${url}"
      return 1
    fi
  done
  echo "[run-local] ${label} healthy at ${url}"
}

show_status() {
  local name="$1"
  local pid_file="$2"

  if is_running "$pid_file"; then
    echo "[run-local] ${name}: running (pid $(cat "$pid_file"))"
  else
    echo "[run-local] ${name}: stopped"
  fi
}

start_all() {
  local localhost_origin="http://localhost:${DASHBOARD_PORT}"
  local loopback_origin="http://127.0.0.1:${DASHBOARD_PORT}"

  API_ALLOWED_ORIGINS="$(merge_origins "${API_ALLOWED_ORIGINS:-}" "$localhost_origin" "$loopback_origin" "http://localhost:1420" "http://127.0.0.1:1420" "tauri://localhost")"
  AGENT_ALLOWED_ORIGINS="$(merge_origins "${AGENT_ALLOWED_ORIGINS:-}" "$localhost_origin" "$loopback_origin" "http://localhost:1420" "http://127.0.0.1:1420" "tauri://localhost")"
  export API_ALLOWED_ORIGINS
  export AGENT_ALLOWED_ORIGINS

  stop_orphan_processes "api" "(/tmp/go-build|\.cache/go-build).*/(api)( |$)"
  stop_orphan_processes "worker" "(/tmp/go-build|\.cache/go-build).*/(worker)( |$)"
  stop_orphan_processes "collector" "(/tmp/go-build|\.cache/go-build).*/(collector)( |$)"

  start_service "api" "$API_PID_FILE" "$API_LOG" "go run ./cmd/api"
  start_service "worker" "$WORKER_PID_FILE" "$WORKER_LOG" "go run ./cmd/worker"
  start_service "collector" "$COLLECTOR_PID_FILE" "$COLLECTOR_LOG" "go run ./cmd/collector"

  if [[ -x "${ROOT_DIR}/.venv/bin/uvicorn" ]]; then
    start_service "agents" "$AGENTS_PID_FILE" "$AGENTS_LOG" ".venv/bin/uvicorn app.main:app --port ${AGENTS_PORT} --app-dir agents"
  else
    echo "[run-local] agents not started (.venv/bin/uvicorn missing). Run bootstrap first."
  fi

  if command -v npm >/dev/null 2>&1; then
    start_service "dashboard" "$DASHBOARD_PID_FILE" "$DASHBOARD_LOG" "CI=true npm run dev --prefix frontend -- --host 127.0.0.1 --port ${DASHBOARD_PORT} --strictPort"
  else
    echo "[run-local] dashboard not started (npm missing). Install Node.js and run bootstrap first."
  fi

  wait_for_http "Go API" "http://127.0.0.1:${API_PORT}/health" 20 || true
  if is_running "$AGENTS_PID_FILE"; then
    wait_for_http "Agents API" "http://127.0.0.1:${AGENTS_PORT}/health" 20 || true
  fi
  if is_running "$DASHBOARD_PID_FILE"; then
    wait_for_http "Dashboard" "http://127.0.0.1:${DASHBOARD_PORT}" 20 || true
  fi

  echo "[run-local] startup complete"
  status_all
}

stop_all() {
  stop_service "dashboard" "$DASHBOARD_PID_FILE"
  stop_service "agents" "$AGENTS_PID_FILE"
  stop_service "collector" "$COLLECTOR_PID_FILE"
  stop_service "worker" "$WORKER_PID_FILE"
  stop_service "api" "$API_PID_FILE"
  echo "[run-local] all services stopped"
}

status_all() {
  show_status "api" "$API_PID_FILE"
  show_status "worker" "$WORKER_PID_FILE"
  show_status "collector" "$COLLECTOR_PID_FILE"
  show_status "agents" "$AGENTS_PID_FILE"
  show_status "dashboard" "$DASHBOARD_PID_FILE"
}

logs_all() {
  echo "[run-local] tailing logs (Ctrl+C to exit)"
  tail -n 120 -f "$API_LOG" "$WORKER_LOG" "$COLLECTOR_LOG" "$AGENTS_LOG" "$DASHBOARD_LOG"
}

COMMAND="${1:-start}"
case "$COMMAND" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  status)
    status_all
    ;;
  logs)
    logs_all
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
