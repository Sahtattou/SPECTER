# SPECTER

Last validated: 2026-03-22 (local ci-check + service orchestration)

SPECTER is a threat-intelligence prototype that ingests public OSINT indicators, normalizes and scores them, and exposes analyst-ready outputs through APIs, an agent service, and a dashboard.

It is designed for a "collect -> validate -> score -> explain -> export" workflow, with a built-in adversarial mirror that simulates poisoning attempts and tracks detection performance.

## Why this project exists

Most student TI demos stop at data collection. SPECTER is built to show an end-to-end pipeline that can:

- collect from multiple OSINT providers,
- run deterministic validation and scoring,
- expose operational APIs for SOC-style workflows,
- generate export artifacts (STIX and report),
- run an adversarial loop (red vs blue style) for pipeline integrity testing.

## Current system capabilities

- Go collector that pulls and processes providers concurrently (`cmd/collector/main.go`)
- Go API server for health, events, metrics, exports, and manual injections (`cmd/api/main.go`, `internal/api/`)
- Go worker service that processes validated records with concurrency + graceful shutdown (`cmd/worker/main.go`)
- SQLite-backed repository with schema initialization and indices (`internal/storage/repository.go`, `internal/storage/migrations/001_init.sql`)
- Python FastAPI agent service with blue/red agent endpoints and adversarial mirror endpoints (`agents/app/main.py`)
- Agent mirror red/blue balancing with auto-red guardrails + Go real-event sync (`agents/app/adversarial/service.py`)
- Tauri + React desktop dashboard consuming agent-service mirror endpoints (`frontend/`)
- Task runners and bootstrap tooling (`justfile`, `Makefile`, `scripts/bootstrap.sh`)

## High-level architecture

```
OSINT Providers (Go)
  crt.sh, Shodan, URLHaus, AbuseIPDB, OTX
          |
          v
Collector + Normalize + Detect + Score (Go)
  cmd/collector -> internal/ingest -> internal/validation -> internal/scoring
          |
          v
Persistence (SQLite)
  internal/storage (threat_records table)
          |
          +------------------------------+
          |                              |
          v                              v
Go REST API                        Python Agent Service
  /api/v1/events, metrics,           /agents/*, /mirror/*
  exports, injections                talks to Go API
          |                              |
          +--------------+---------------+
                         |
                         v
              Tauri + React Desktop Dashboard
```

## Repository layout

```text
SPECTER/
├── cmd/
│   ├── api/            # Go API server entrypoint
│   ├── collector/      # Go collection + pipeline processing
│   └── worker/         # Worker runtime service (validated -> scored processing)
├── internal/
│   ├── api/            # HTTP handlers and router
│   ├── config/         # Env-based runtime config
│   ├── ingest/         # Normalization/dedup helpers
│   ├── output/         # STIX/report exporters
│   ├── providers/      # External OSINT provider collectors
│   ├── scoring/        # Threat scoring logic
│   ├── storage/        # SQLite repository + migration
│   └── validation/     # Detection/quarantine rules
├── pkg/models/         # Shared domain models
├── agents/             # Python FastAPI agents service
├── frontend/           # Tauri + React desktop dashboard
├── scripts/            # Bootstrap and local run helpers
├── justfile            # Developer task runner (dotenv-aware)
├── Makefile            # Build/test task runner (CI friendly)
└── .env.example        # Environment template
```

## Prerequisites

- Go 1.24+
- Python 3.11+
- Node.js 18+
- Rust toolchain (for Tauri desktop build)
- Bash (Linux/macOS shell)

Optional but recommended:

- `just` for local developer commands
- `make` for CI-style or conventional build workflows

## Task runner separation of concerns

This repository supports both `make` and `just`.

They intentionally overlap for most targets (`build`, `check`, `run-local`, `run-agents`, `run-dashboard`, `test`). The practical separation is:

- `make`: conventional build/CI entrypoint, especially useful in CI and automation pipelines.
- `just`: local developer convenience with automatic `.env` loading.

Important behavior difference:

- `justfile` has `dotenv-load := true`, so `just` auto-loads `.env` into recipe processes.
- `Makefile` does not auto-load `.env`; it uses variables already exported in your shell.

Suggested usage:

- Compile and finalization checks: `make build`, `make check`
- Local developer scripts and orchestration: `just run-local`, `just run-agents`, `just run-dashboard`

Type `just` to see the full just command list.

## Quick start

Operational runbook: `docs/RUNNING_GUIDE.md`
Active task tracker: `TEAM_TASK_LIST.md`

### 1) Full bootstrap (recommended)

```bash
./scripts/bootstrap.sh
```

What this does:

- verifies `go` and `python3` are installed,
- creates `.env` from `.env.example` if missing,
- creates `.venv` if missing,
- installs Python dependencies,
- downloads Go modules,
- builds Go binaries,
- runs baseline Go and Python tests.

Before starting services, verify local DB mode in `.env`:

```bash
DB_DSN=file:specter.db?_busy_timeout=5000&_journal_mode=WAL
```

The current runtime storage implementation is SQLite-backed.

### 2) Start services

Single-command local orchestration:

```bash
./scripts/run_local.sh start
```
or

```bash
make run-local
```

This starts Go API + worker + collector + agents + React dev dashboard with pid/log supervision.
You can still run services individually (`make run-agents`, `make run-dashboard`) for debugging.

Service orchestration helpers:

```bash
./scripts/run_local.sh status
./scripts/run_local.sh logs
./scripts/run_local.sh stop
./scripts/run_local.sh restart
```

Equivalent Make/Just targets:
- `make status-local` / `just status-local`
- `make logs-local` / `just logs-local`
- `make stop-local` / `just stop-local`
- `make restart-local` / `just restart-local`

### 2.1) Optional demo prep and rehearsal

```bash
./scripts/seed_demo_data.sh
./scripts/agent_smoke.sh
./scripts/rehearse_demo.sh
```

These scripts seed realistic demo IOC records, validate agent workflow paths (blue, red, run, mirror ingest), and run a smoke rehearsal path (health checks, seed, mirror trigger, exports).

### 2.2) Reliability command profile

```bash
make ci-check
# or
just ci-check
```

This runs the CI-equivalent local quality profile: Go tests, Python tests, contract tests (temporary Go API fixture), compile checks, and shell script syntax checks.

### 2.3) Offline fallback and bundle generation

```bash
./scripts/load_offline_snapshot.sh
./scripts/create_artifact_bundle.sh
```

Or use task runners:

```bash
make offline-load
make bundle
# or
just offline-load
just bundle
```

### 3) Health checks

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8001/health
```

## Manual setup (without bootstrap script)

```bash
cp .env.example .env
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r agents/requirements.txt
.venv/bin/python -m pip install pytest requests
npm install --prefix frontend
go mod download
```

## Configuration

Environment loading behavior differs by entrypoint:

- Go services load `.env` through `godotenv` in `internal/config/config.go`.
- `just` auto-loads `.env` because `justfile` enables `dotenv-load`.
- `make`, direct `uvicorn`, and direct `npm` commands do not auto-parse `.env`; they use exported shell variables and code defaults.

### Core runtime variables

| Variable | Purpose | Default in code |
|---|---|---|
| `API_PORT` | Go API listen port | `8080` |
| `API_ALLOWED_ORIGINS` | Allowed browser/webview origins for Go API CORS | empty |
| `WORKER_CONCURRENCY` | Worker parallelism setting | `4` |
| `COLLECTION_INTERVAL_SECONDS` | Collector tick interval | `60` |
| `DB_DSN` | SQLite DSN | `file:specter.db?_busy_timeout=5000&_journal_mode=WAL` |
| `ABUSEIPDB_API_KEY` | AbuseIPDB provider key | empty |
| `OTX_API_KEY` | OTX provider key | empty |
| `SHODAN_API_KEY` | Shodan provider key | empty |
| `URLHAUS_API_KEY` | URLHaus provider key | empty |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEMO_MODE` | Demo-mode toggle (no implicit provider seeds) | `false` |
| `SHODAN_TARGETS` | Comma-separated Shodan collector targets | empty |
| `ABUSEIPDB_TARGETS` | Comma-separated AbuseIPDB collector targets | empty |
| `OTX_TARGETS` | Comma-separated OTX collector targets | empty |
| `URLHAUS_HOSTS` | Comma-separated URLHaus host targets | empty |
| `CRTSH_QUERY` | crt.sh query string | empty |
| `ENABLE_SHODAN` | Hard disable Shodan provider even if targets/key exist | `true` |
| `ENABLE_ABUSEIPDB` | Hard disable AbuseIPDB provider even if targets/key exist | `true` |
| `ENABLE_OTX` | Hard disable OTX provider even if targets/key exist | `true` |
| `ENABLE_URLHAUS` | Hard disable URLHaus provider even if targets/key exist | `true` |
| `ENABLE_CRTSH` | Hard disable crt.sh provider even if query exists | `true` |
| `CRTSH_DEDUPLICATE` | Add `deduplicate=Y` for crt.sh query | `true` |
| `CRTSH_EXCLUDE_EXPIRED` | Add `exclude=expired` for crt.sh query | `true` |
| `CRTSH_MAX_RESULTS` | Max unique domains accepted per crt.sh collection run (`0` = no cap) | `1000` |

Collector note:

- Providers with empty target lists are skipped.
- Providers requiring API keys are skipped if targets are set but keys are missing (collector logs a clear skip reason).
- Providers can be explicitly disabled regardless of target lists via `ENABLE_*` flags.

Rate-limit and plan-limit note:

- AbuseIPDB `429 Too Many Requests` now causes temporary provider cooldown instead of immediate retry each tick.
- Shodan plan/auth errors (e.g. `Requires membership or higher`) now trigger extended suppression (24h) to reduce noise.
- You can immediately mute noisy providers with:

```bash
ENABLE_ABUSEIPDB=false
ENABLE_SHODAN=false
```

### Agents service variables

| Variable | Purpose | Default |
|---|---|---|
| `GO_API_BASE_URL` | Go API base URL used by agents | `http://localhost:8080` |
| `AGENT_ALLOWED_ORIGINS` | Allowed browser/webview origins for Agents API CORS | `http://localhost:1420,tauri://localhost` |
| `AGENT_REQUEST_TIMEOUT_SECONDS` | HTTP timeout to Go API | `10` |
| `AGENT_MAX_RETRIES` | Retries for agent HTTP calls | `2` |
| `AGENT_MODEL` | Agent model label/config | `gpt-4.1-mini` |
| `RED_AGENT_INTERVAL_SECONDS` | Red agent background interval | `30` |
| `RED_MAX_RATIO` | Max allowed auto red ratio (`injections/real_events`) | `1.0` |
| `MIN_REAL_EVENTS_BEFORE_AUTO_RED` | Auto red waits for baseline real telemetry | `5` |
| `GO_SYNC_INTERVAL_SECONDS` | Agent mirror sync interval for Go real events | `15` |
| `GO_SYNC_BATCH_LIMIT` | Max Go events fetched per sync cycle | `20` |
| `GO_SYNC_ON_STARTUP` | Run first Go sync immediately on service start | `false` |
| `ADVERSARIAL_DB_PATH` | Adversarial mirror sqlite path | `./specter_adversarial.db` |

### Desktop dashboard variables

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_API_BASE_URL` | Agent API base URL used by dashboard requests | `http://localhost:8001` |
| `VITE_AGENT_API_BASE_URL` | Agent API base URL used by React frontend | `http://127.0.0.1:8001` |
| `VITE_GO_API_BASE_URL` | Go API base URL used by React frontend | `http://127.0.0.1:8080` |

Note about `DB_DSN`:

- Runtime defaults are SQLite-backed (`internal/config/config.go` + `internal/storage` migration path).
- For local usage, keep `DB_DSN=file:specter.db?_busy_timeout=5000&_journal_mode=WAL` unless you intentionally run another backend.

## API surfaces

### Go API (default `:8080`)

Defined in `internal/api/router.go`:

- `GET /health`
- `GET /api/v1/events`
- `GET /api/v1/events/quarantined`
- `GET /api/v1/metrics/pipeline`
- `POST /api/v1/exports/stix`
- `POST /api/v1/exports/report`
- `POST /api/v1/agents/injections/trigger`

`GET /api/v1/metrics/pipeline` now includes freshness fields to verify continuous pulls under upsert-heavy workloads:

- `last_collected_at`
- `last_updated_at`
- `freshness_age_seconds`
- `distinct_sources`
- `source_freshness_age_seconds`

### Agents API (default `:8001`)

Defined in `agents/app/main.py`:

- `GET /health`
- `GET /ready`
- `POST /mirror/ingest`
- `POST /mirror/injections/trigger`
- `POST /api/v1/agents/injections/trigger` (alias)
- `GET /mirror/events`
- `GET /mirror/injections`
- `GET /mirror/metrics`
- `GET /mirror/dashboard` (atomic snapshot for metrics + feed + injections)
- `POST /mirror/exports/stix` (STIX generated from same mirror snapshot)
- `POST /mirror/exports/report` (report/PDF generated from same mirror snapshot)

Dashboard sync note:

- The React/Tauri dashboard now uses `GET /mirror/dashboard` so Pipeline Overview and Live IOC Feed are rendered from one agents-side snapshot (`snapshot_generated_at`) to avoid cross-endpoint drift.
- STIX/report exports now use this same mirror snapshot contract and embed snapshot metadata (`snapshot_generated_at`, derived snapshot id basis) for anti-drift traceability.
- In snapshot metrics, `total_events` is pipeline-aligned (from Go pipeline metrics when reachable), while `mirror_total_events` preserves the local mirror event count.
- `POST /agents/blue/analyze`
- `POST /agents/red/inject`
- `POST /agents/run`

## Build, run, and test commands

### Make (build/finalization oriented)

```bash
make help
make bootstrap
make build
make check
make test
make clean
```

### Just (developer scripts and local operations)

```bash
just
just setup
just run-local
just run-agents
just run-dashboard
just build-dashboard
just check
```

`build-dashboard` targets Linux `deb` and `rpm` bundles by default for reproducible packaging in environments where AppImage tooling may be unavailable.

Optional AppImage build (Linux):

```bash
npm run tauri --prefix frontend -- build --bundles appimage
```

### Script-level shortcuts

```bash
./scripts/bootstrap.sh
./scripts/run_local.sh
./scripts/seed_demo_data.sh
```

## Exports and artifacts

- STIX export writes timestamped files to `artifacts/stix/`.
- Report export writes timestamped files to `artifacts/reports/`.
- Report export now writes a valid PDF structure with metrics, legend, and highlight sections.

## Testing and quality

Go:

```bash
go fmt ./...
go vet ./...
go test ./... -v
```

Python agents:

```bash
.venv/bin/python -m pytest agents/tests
```

Or run unified checks:

```bash
make check
# or
just check
```

## Operational notes and caveats

- `scripts/run_local.sh` now orchestrates API/worker/collector/agents/dashboard with `start|stop|status|logs|restart`.
- Network-dependent provider tests may be slow or occasionally skip/pass differently depending on upstream availability.
- Contract tests spin a temporary Go API process in `agents/tests/conftest.py`.
- `scripts/seed_demo_data.sh`, `scripts/agent_smoke.sh`, and `scripts/rehearse_demo.sh` are live operational scripts.

## Documentation footprint (minimal)

Only keep and maintain these documents as source-of-truth:

- `README.md` (overview, setup, API surface summary, troubleshooting)
- `docs/RUNNING_GUIDE.md` (operational run sequence and demo/verification flows)
- `TEAM_TASK_LIST.md` (current backlog and ownership)

All historical audit/sprint planning notes are intentionally removed to keep maintenance overhead low.

## Troubleshooting

### Go API fails to start with database issues

Ensure `DB_DSN` is SQLite-compatible for local runs:

```bash
DB_DSN=file:specter.db?_busy_timeout=5000&_journal_mode=WAL
```

### Python commands fail because `.venv` is missing

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r agents/requirements.txt
```

### Desktop dashboard cannot fetch data

Verify both dependencies are up:

- Go API reachable at `http://localhost:8080/health`
- Agents service reachable at `http://localhost:8001/health`

If APIs are healthy but frontend requests fail, verify `API_ALLOWED_ORIGINS` and `AGENT_ALLOWED_ORIGINS` include your dashboard origin(s):

```bash
API_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420,tauri://localhost
AGENT_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420,tauri://localhost
```

### Desktop app launch

Run the Tauri desktop app:

```bash
npm run tauri dev --prefix frontend
```

### Service startup reproducibility check

Run this after fresh setup to verify documentation flow end-to-end:

```bash
./scripts/run_local.sh start
./scripts/run_local.sh status
./scripts/seed_demo_data.sh
./scripts/agent_smoke.sh
./scripts/rehearse_demo.sh
make ci-check
```

### `make` command does not see `.env`

Use `just` (auto dotenv) or export variables in your shell before `make`.

## License

This project is licensed under the terms in `LICENSE`.
