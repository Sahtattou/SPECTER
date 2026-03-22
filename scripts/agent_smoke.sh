#!/usr/bin/env bash
set -euo pipefail

AGENT_API_BASE_URL="${AGENT_API_BASE_URL:-http://localhost:8001}"

post_json() {
  local path="$1"
  local payload="$2"
  curl -sS -X POST "${AGENT_API_BASE_URL}${path}" \
    -H "Content-Type: application/json" \
    -d "$payload"
}

echo "[agent-smoke] health"
curl -sS "${AGENT_API_BASE_URL}/health" >/dev/null

echo "[agent-smoke] mirror ingest (non-injection path)"
post_json "/mirror/ingest" '{
  "ioc_type":"domain",
  "raw_value":"demo-ingest-safe.example",
  "source_name":"collector_sim",
  "raw_evidence":{"domain_age_days":45},
  "corroboration_count":2,
  "collected_at":"2026-03-22T10:00:00Z"
}' >/dev/null

echo "[agent-smoke] blue analyze"
post_json "/agents/blue/analyze" '{"limit":20}' >/dev/null

echo "[agent-smoke] red inject dry-run"
post_json "/agents/red/inject" '{"attack_type":"GHOST_DOMAIN","dry_run":true}' >/dev/null

echo "[agent-smoke] red inject live submit"
post_json "/agents/red/inject" '{"attack_type":"TTP_MISMATCH","dry_run":false}' >/dev/null

echo "[agent-smoke] generic agent runner: blue"
post_json "/agents/run" '{"agent_name":"blue_analyst","limit":20,"dry_run":true}' >/dev/null

echo "[agent-smoke] generic agent runner: red"
post_json "/agents/run" '{"agent_name":"red_injector","limit":20,"dry_run":true}' >/dev/null

echo "[agent-smoke] mirror metrics snapshot"
curl -sS "${AGENT_API_BASE_URL}/mirror/metrics"
echo

echo "[agent-smoke] complete"
