# SPECTER Running Guide

This guide is the operational reference for local runs, demo rehearsal, offline fallback, and submission packaging.

Last validated: 2026-03-22 (local run + ci-check)
Validation context: current `main` workspace state

Command quick-reference: see `README.md` sections "Quick start" and "Build, run, and test commands".

## 1) Start core services

### Go stack

```bash
./scripts/run_local.sh start
```

To collect real telemetry, configure at least one provider target set in `.env` (examples):

```bash
SHODAN_TARGETS=1.1.1.1,8.8.8.8
ABUSEIPDB_TARGETS=1.1.1.1
OTX_TARGETS=example.org,1.1.1.1
URLHAUS_HOSTS=example.org
CRTSH_QUERY=%.example.org
```

If target lists are empty, collector runs but has no real-source pull workload.

Management commands:

```bash
./scripts/run_local.sh status
./scripts/run_local.sh logs
./scripts/run_local.sh stop
./scripts/run_local.sh restart
```

### Agents service

```bash
.venv/bin/uvicorn app.main:app --reload --port ${AGENTS_PORT:-8001} --app-dir agents
```

### Dashboard

```bash
.venv/bin/streamlit run dashboards/streamlit_app.py
```

## 2) Reliability checks (local CI profile)

```bash
make ci-check
# or
just ci-check
```

Includes:
- Go tests
- Python tests (including contract tests with temporary Go API fixture)
- Python compile checks
- shell script syntax validation

## 3) Demo preparation

### Seed realistic live demo data

```bash
./scripts/seed_demo_data.sh
```

### Validate agent workflow scripts (not injection-only)

```bash
./scripts/agent_smoke.sh
```

This smoke script validates:
- `/mirror/ingest` (non-injection ingest path)
- `/agents/blue/analyze`
- `/agents/red/inject` (dry and live)
- `/agents/run` for both `blue_analyst` and `red_injector`
- `/mirror/metrics`

### Run demo rehearsal smoke flow

```bash
./scripts/rehearse_demo.sh
```

`rehearse_demo.sh` now includes `agent_smoke.sh`, so rehearsal verifies full agent workflow coverage in addition to injection and export paths.

Expected rehearsal checkpoints:
- Go API health passes
- Agents health passes
- Seed completes
- Agent smoke completes (blue/red/run/mirror ingest)
- Mirror metrics endpoint responds
- STIX and report export endpoints respond

## 4) Offline fallback mode

When internet/services are degraded, use snapshot-driven dataset load:

```bash
./scripts/load_offline_snapshot.sh
```

Default snapshot file:
- `data/offline/demo_snapshot.json`

Override with:

```bash
SNAPSHOT_PATH=/path/to/snapshot.json ./scripts/load_offline_snapshot.sh
```

## 5) Submission artifact bundle

Generate bundle skeleton + export responses + copied artifacts:

```bash
./scripts/create_artifact_bundle.sh
```

Output:
- `artifacts/submission_bundle/<timestamp>/`
  - `stix/`
  - `reports/`
  - `screenshots/`
  - `video/`
  - `CHECKLIST.md`

## 6) Dashboard reliability controls

Environment kill switches:

```bash
export DISABLE_AUTO_REFRESH=true
export DISABLE_PRESENTATION_MODE=true
```

These disable auto-refresh and presentation mode toggles for emergency stabilization.

## 7) Red/Blue balance controls (important)

To avoid red-heavy skew when real telemetry is low, tune these env vars for the agents service:

```bash
export RED_AGENT_INTERVAL_SECONDS=30
export RED_MAX_RATIO=1.0
export MIN_REAL_EVENTS_BEFORE_AUTO_RED=5
export GO_SYNC_INTERVAL_SECONDS=15
export GO_SYNC_BATCH_LIMIT=20
export GO_SYNC_ON_STARTUP=false
```

Meaning:
- `RED_MAX_RATIO`: max allowed `injections / real_events` for automatic red loop.
- `MIN_REAL_EVENTS_BEFORE_AUTO_RED`: red auto-loop waits until this many real events exist.
- `GO_SYNC_INTERVAL_SECONDS`: how often agents pull recent Go events into mirror as blue real telemetry.
- `GO_SYNC_BATCH_LIMIT`: max Go events pulled per sync cycle (reduces burst size).
- `GO_SYNC_ON_STARTUP`: if `false`, skips immediate first sync cycle at process start.

Manual red trigger endpoints still work regardless of auto-loop guardrails.

## 8) Common failure modes (symptom -> cause -> fix)

1. **Red dominates Blue in dashboard**
   - Cause: low real telemetry baseline and auto-red loop still active.
   - Fix: tune `RED_MAX_RATIO`, `MIN_REAL_EVENTS_BEFORE_AUTO_RED`, and `GO_SYNC_INTERVAL_SECONDS`; verify `/mirror/metrics` balance fields.

2. **`create_artifact_bundle.sh` fails JSON parse/export**
   - Cause: Go export endpoint not healthy or non-JSON error response.
   - Fix: check `http://localhost:8080/health`, then retry; script now prints HTTP/body diagnostics.

3. **Contract tests fail to collect**
   - Cause: environment process conflict or temp Go API startup failure.
   - Fix: run `./scripts/run_local.sh status`, stop conflicting processes, rerun `make ci-check`.

4. **Dashboard shows stale/empty data**
   - Cause: agents service unavailable or mirror database newly initialized.
   - Fix: verify `http://localhost:8001/health`, then run `./scripts/seed_demo_data.sh` and `./scripts/agent_smoke.sh`.
   - Refresh note: dashboard auto-refresh defaults to a live interval now (10s). If manually set to `0`, ingestion panels will not update until manual rerun.
   - Metrics note: `GET /mirror/metrics` now returns freshness signals (`metrics_generated_at`, `last_event_updated_at`, `freshness_age_seconds`, `source_freshness_age_seconds`) that the dashboard renders in Pipeline Metrics.
   - Count accuracy note: pipeline totals (`Total`, `Scored`, `Quarantined`) are sourced from Go API `GET /api/v1/metrics/pipeline`; red/injection dynamics remain sourced from agents `GET /mirror/metrics`.

5. **Local run command starts only partial services**
   - Cause: missing `.venv/bin/uvicorn` or `.venv/bin/streamlit`.
   - Fix: run `./scripts/bootstrap.sh` and restart with `./scripts/run_local.sh restart`.

6. **Real telemetry appears stale or only example data shows up**
   - Cause: collector targets are deterministic seeds or empty target lists; multiple orphan collectors can also overwrite visibility.
   - Fix: set explicit non-demo targets in `.env` (`SHODAN_TARGETS`, `ABUSEIPDB_TARGETS`, `OTX_TARGETS`, `URLHAUS_HOSTS`, `CRTSH_QUERY`), keep `DEMO_MODE=false`, and restart with `./scripts/run_local.sh restart`.

7. **Looks like collector only pulled once after startup**
   - Cause: total-event counts can stay flat under upsert, even while rows are refreshed.
   - Fix: check freshness fields on `GET /api/v1/metrics/pipeline` (`last_updated_at`, `freshness_age_seconds`, `source_freshness_age_seconds`) to confirm ongoing pulls.
