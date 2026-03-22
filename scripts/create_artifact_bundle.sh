#!/usr/bin/env bash
set -euo pipefail

GO_API_BASE_URL="${GO_API_BASE_URL:-http://localhost:8080}"
BUNDLE_ROOT="${BUNDLE_ROOT:-artifacts/submission_bundle}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
BUNDLE_DIR="${BUNDLE_ROOT}/${STAMP}"

mkdir -p "${BUNDLE_DIR}/stix" "${BUNDLE_DIR}/reports" "${BUNDLE_DIR}/screenshots" "${BUNDLE_DIR}/video"

parse_artifact_path() {
  local json_payload="$1"
  local label="$2"
  local parsed
  parsed="$(python3 - <<'PY' "$json_payload"
import json
import sys

payload = sys.argv[1]
try:
    data = json.loads(payload)
except json.JSONDecodeError as exc:
    print(f"JSON_ERROR::{exc}")
    raise SystemExit(1)

if not isinstance(data, dict):
    print("JSON_ERROR::response_not_object")
    raise SystemExit(1)

print(data.get("artifact_path", ""))
PY
  )" || {
    echo "[bundle] ERROR: ${label} response was not valid JSON."
    echo "[bundle] raw response: ${json_payload}"
    exit 1
  }
  printf '%s' "$parsed"
}

call_export() {
  local endpoint="$1"
  local label="$2"
  local body_file
  body_file="$(mktemp)"

  local http_code
  http_code="$(curl -sS -o "$body_file" -w '%{http_code}' -X POST "${GO_API_BASE_URL}${endpoint}")"
  local body
  body="$(cat "$body_file")"
  rm -f "$body_file"

  if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
    echo "[bundle] ERROR: ${label} export failed (HTTP ${http_code})."
    echo "[bundle] response body: ${body}"
    exit 1
  fi

  printf '%s' "$body"
}

echo "[bundle] generating exports via Go API"
stix_json="$(call_export "/api/v1/exports/stix" "STIX")"
report_json="$(call_export "/api/v1/exports/report" "Report")"

echo "$stix_json" > "${BUNDLE_DIR}/stix_export_response.json"
echo "$report_json" > "${BUNDLE_DIR}/report_export_response.json"

stix_path="$(parse_artifact_path "$stix_json" "STIX")"
report_path="$(parse_artifact_path "$report_json" "Report")"

if [ -n "$stix_path" ] && [ -f "$stix_path" ]; then
  cp "$stix_path" "${BUNDLE_DIR}/stix/"
else
  echo "[bundle] warning: STIX artifact path missing or file not found (${stix_path:-none})"
fi

if [ -n "$report_path" ] && [ -f "$report_path" ]; then
  cp "$report_path" "${BUNDLE_DIR}/reports/"
else
  echo "[bundle] warning: Report artifact path missing or file not found (${report_path:-none})"
fi

cat > "${BUNDLE_DIR}/CHECKLIST.md" <<'EOF'
# Submission Bundle Checklist

- [ ] STIX sample present in `stix/`
- [ ] Report sample present in `reports/`
- [ ] Dashboard screenshots added to `screenshots/`
- [ ] 2-minute demo video added to `video/` (placeholder present)
- [ ] Final review notes captured
EOF

cat > "${BUNDLE_DIR}/video/README.txt" <<'EOF'
Place the final 2-minute demo video file here.
Suggested name: specter_demo_2min.mp4
EOF

echo "[bundle] created at ${BUNDLE_DIR}"
