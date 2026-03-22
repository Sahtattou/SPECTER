#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf "Error: required command '%s' is not installed or not in PATH.\n" "$cmd" >&2
    exit 1
  fi
}

printf "==> Verifying required tooling...\n"
require_cmd go
require_cmd python3
require_cmd npm

printf "==> Go version: %s\n" "$(go version)"
printf "==> Python version: %s\n" "$(python3 --version)"
printf "==> Node version: %s\n" "$(node --version)"

if [ ! -f .env ]; then
  printf "==> Creating .env from .env.example\n"
  cp .env.example .env
else
  printf "==> .env already exists, leaving it unchanged\n"
fi

if [ ! -d .venv ]; then
  printf "==> Creating Python virtual environment (.venv)\n"
  python3 -m venv .venv
else
  printf "==> .venv already exists\n"
fi

printf "==> Upgrading pip/setuptools/wheel\n"
.venv/bin/python -m pip install --upgrade pip setuptools wheel

printf "==> Installing Python dependencies\n"
.venv/bin/python -m pip install -r agents/requirements.txt
.venv/bin/python -m pip install pytest requests

printf "==> Installing frontend dependencies\n"
npm install --prefix frontend

printf "==> Downloading Go modules\n"
go mod download

printf "==> Building Go binaries\n"
mkdir -p bin
go build -o ./bin/api ./cmd/api
go build -o ./bin/worker ./cmd/worker
go build -o ./bin/collector ./cmd/collector

printf "==> Running baseline checks\n"
go test ./... -v
.venv/bin/python -m pytest agents/tests

cat <<'EOF'

Bootstrap completed successfully.

Next steps:
  1) Edit .env as needed (API keys, ports, DB settings)
  2) Start core Go services: ./scripts/run_local.sh
  3) Start agents API: .venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents
  4) Start desktop dashboard: npm run tauri dev --prefix frontend

Optional task runners:
  - just check
  - make check
EOF
