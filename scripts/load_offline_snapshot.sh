#!/usr/bin/env bash
set -euo pipefail

GO_API_BASE_URL="${GO_API_BASE_URL:-http://localhost:8080}"
SNAPSHOT_PATH="${SNAPSHOT_PATH:-data/offline/demo_snapshot.json}"

if [ ! -f "$SNAPSHOT_PATH" ]; then
  echo "[offline] snapshot not found: $SNAPSHOT_PATH" >&2
  exit 1
fi

echo "[offline] loading snapshot from $SNAPSHOT_PATH into $GO_API_BASE_URL"

python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

import requests

base = os.getenv("GO_API_BASE_URL", "http://localhost:8080").rstrip("/")
snapshot_path = Path(os.getenv("SNAPSHOT_PATH", "data/offline/demo_snapshot.json"))
payloads = json.loads(snapshot_path.read_text(encoding="utf-8"))

for idx, payload in enumerate(payloads, start=1):
    resp = requests.post(f"{base}/api/v1/agents/injections/trigger", json=payload, timeout=10)
    resp.raise_for_status()
    body = resp.json()
    print(f"[{idx}/{len(payloads)}] submitted={body.get('submitted')} event_id={body.get('event_id')}")

metrics = requests.get(f"{base}/api/v1/metrics/pipeline", timeout=10)
metrics.raise_for_status()
print("metrics:", metrics.json())
PY

echo "[offline] snapshot load complete"
