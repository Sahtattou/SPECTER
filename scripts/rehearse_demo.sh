#!/usr/bin/env bash
set -euo pipefail

GO_API_BASE_URL="${GO_API_BASE_URL:-http://localhost:8080}"
AGENT_API_BASE_URL="${AGENT_API_BASE_URL:-http://localhost:8001}"

echo "[rehearse] checking service health"
curl -sS "${GO_API_BASE_URL}/health" >/dev/null
curl -sS "${AGENT_API_BASE_URL}/health" >/dev/null

echo "[rehearse] seeding realistic demo data"
"$(dirname "$0")/seed_demo_data.sh" >/dev/null

echo "[rehearse] triggering mirror injection"
curl -sS -X POST "${AGENT_API_BASE_URL}/mirror/injections/trigger" \
  -H "Content-Type: application/json" \
  -d '{"attack_type":"GHOST_DOMAIN"}' >/dev/null

echo "[rehearse] fetching mirror metrics"
curl -sS "${AGENT_API_BASE_URL}/mirror/metrics"
echo

echo "[rehearse] exporting STIX and report"
curl -sS -X POST "${GO_API_BASE_URL}/api/v1/exports/stix"
echo
curl -sS -X POST "${GO_API_BASE_URL}/api/v1/exports/report"
echo

echo "[rehearse] done"
