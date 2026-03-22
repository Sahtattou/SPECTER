# SPECTER Running Guide

This guide is the operational reference for local runs, demo rehearsal, offline fallback, and submission packaging.

## 1) Start core services

### Go stack

```bash
./scripts/run_local.sh start
```

Management commands:

```bash
./scripts/run_local.sh status
./scripts/run_local.sh logs
./scripts/run_local.sh stop
./scripts/run_local.sh restart
```

### Agents service

```bash
.venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents
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
