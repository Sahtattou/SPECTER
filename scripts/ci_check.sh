#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[ci-check] go test"
go test ./...

echo "[ci-check] python tests"
python3 -m pytest agents/tests

echo "[ci-check] contract-only tests"
python3 -m pytest -m contract agents/tests

echo "[ci-check] python syntax compile"
python3 -m compileall agents/app agents/tests dashboards

echo "[ci-check] shell script syntax"
bash -n scripts/bootstrap.sh
bash -n scripts/run_local.sh
bash -n scripts/seed_demo_data.sh
bash -n scripts/rehearse_demo.sh
bash -n scripts/load_offline_snapshot.sh
bash -n scripts/create_artifact_bundle.sh
bash -n scripts/agent_smoke.sh

echo "[ci-check] done"
