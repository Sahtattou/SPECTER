# SPECTER Running Guide

This guide is the operational reference for local runs, demo rehearsal, offline fallback, and submission packaging.

## 1) Start core services

### Go stack

```bash
./scripts/run_local.sh
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

### Run demo rehearsal smoke flow

```bash
./scripts/rehearse_demo.sh
```

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
