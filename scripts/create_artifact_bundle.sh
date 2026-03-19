#!/usr/bin/env bash
set -euo pipefail

GO_API_BASE_URL="${GO_API_BASE_URL:-http://localhost:8080}"
BUNDLE_ROOT="${BUNDLE_ROOT:-artifacts/submission_bundle}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
BUNDLE_DIR="${BUNDLE_ROOT}/${STAMP}"

mkdir -p "${BUNDLE_DIR}/stix" "${BUNDLE_DIR}/reports" "${BUNDLE_DIR}/screenshots" "${BUNDLE_DIR}/video"

echo "[bundle] generating exports via Go API"
stix_json="$(curl -sS -X POST "${GO_API_BASE_URL}/api/v1/exports/stix")"
report_json="$(curl -sS -X POST "${GO_API_BASE_URL}/api/v1/exports/report")"

echo "$stix_json" > "${BUNDLE_DIR}/stix_export_response.json"
echo "$report_json" > "${BUNDLE_DIR}/report_export_response.json"

stix_path="$(python3 - <<'PY'
import json,sys
data=json.loads(sys.stdin.read())
print(data.get('artifact_path',''))
PY
<<< "$stix_json")"

report_path="$(python3 - <<'PY'
import json,sys
data=json.loads(sys.stdin.read())
print(data.get('artifact_path',''))
PY
<<< "$report_json")"

if [ -n "$stix_path" ] && [ -f "$stix_path" ]; then
  cp "$stix_path" "${BUNDLE_DIR}/stix/"
fi

if [ -n "$report_path" ] && [ -f "$report_path" ]; then
  cp "$report_path" "${BUNDLE_DIR}/reports/"
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
