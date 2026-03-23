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
ENABLE_SHODAN=true
ENABLE_ABUSEIPDB=true
ENABLE_OTX=true
ENABLE_URLHAUS=true
ENABLE_CRTSH=true
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

### Desktop dashboard

```bash
npm run tauri dev --prefix frontend
```

Linux packaging (default project workflow):

```bash
make build-dashboard
# or
just build-dashboard
```

This builds `deb` and `rpm` bundles by default.
If you need AppImage explicitly:

```bash
npm run tauri --prefix frontend -- build --bundles appimage
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

## 6) Desktop dashboard connectivity controls

When running the React/Tauri desktop frontend, ensure CORS origins include your local UI origin:

```bash
export API_ALLOWED_ORIGINS=http://localhost:5173,tauri://localhost
export AGENT_ALLOWED_ORIGINS=http://localhost:5173,tauri://localhost
```

Recommended local-safe allowlist (covers both `localhost` and `127.0.0.1` origins used by Vite/Tauri/dev tools):

```bash
export API_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420,tauri://localhost
export AGENT_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420,tauri://localhost
```

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

4. **Desktop dashboard shows stale/empty data**
   - Cause: agents service unavailable or mirror database newly initialized.
   - Fix: verify `http://localhost:8001/health`, then run `./scripts/seed_demo_data.sh` and `./scripts/agent_smoke.sh`.
   - Refresh note: desktop dashboard auto-refresh defaults to a live interval (10s).
   - Snapshot note: dashboard metrics + feed now come from a single agents snapshot endpoint `GET /mirror/dashboard` (includes `snapshot_generated_at`, `metrics`, `events`, `injections`) to keep views synchronized.
   - Export note: `POST /mirror/exports/stix` and `POST /mirror/exports/report` are generated from the same snapshot source so artifact counts align with UI snapshot views.
   - Total-count note: snapshot `metrics.total_events` is now pipeline-aligned using Go pipeline metrics when available; `metrics.mirror_total_events` retains the local mirror-db event count.

5. **Local run command starts only partial services**
   - Cause: missing `.venv/bin/uvicorn` or `npm` frontend dependencies.
   - Fix: run `./scripts/bootstrap.sh` and restart with `./scripts/run_local.sh restart`.

6. **Dashboard log shows Node `read EIO` / unhandled readline error**
   - Cause: frontend dev server started without detached non-interactive stdin in background orchestration.
   - Fix: use `./scripts/run_local.sh start` (current launcher detaches dashboard with `setsid`/`nohup` and redirects stdin from `/dev/null`); then confirm `./scripts/run_local.sh status` and check `logs/dashboard.log`.

7. **Real telemetry appears stale or only example data shows up**
   - Cause: collector targets are deterministic seeds or empty target lists; multiple orphan collectors can also overwrite visibility.
   - Fix: set explicit non-demo targets in `.env` (`SHODAN_TARGETS`, `ABUSEIPDB_TARGETS`, `OTX_TARGETS`, `URLHAUS_HOSTS`, `CRTSH_QUERY`), keep `DEMO_MODE=false`, and restart with `./scripts/run_local.sh restart`.

8. **Looks like collector only pulled once after startup**
   - Cause: unique-event totals can stay flat under upsert even while new ingest runs are being processed.
   - Fix: check both dimensions:
     - `metrics.total_events` / `metrics.pipeline_run_total` in `GET /mirror/dashboard`
     - freshness fields on `GET /api/v1/metrics/pipeline` (`last_updated_at`, `freshness_age_seconds`, `source_freshness_age_seconds`).

9. **Collector repeats `429 Too Many Requests` or Shodan membership errors every cycle**
   - Cause: upstream rate limit or account capability restrictions.
   - Fix:
     - For temporary muting: set `ENABLE_ABUSEIPDB=false` and/or `ENABLE_SHODAN=false`, then `./scripts/run_local.sh restart`.
     - For permanent operation: lower target volume and verify paid plan/API key capability.
   - Behavior note: collector now applies provider cooldown/suppression for rate-limited and permanent auth/capability errors.
