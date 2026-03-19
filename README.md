# SPECTER

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
- SQLite-backed repository with schema initialization and indices (`internal/storage/repository.go`, `internal/storage/migrations/001_init.sql`)
- Python FastAPI agent service with blue/red agent endpoints and adversarial mirror endpoints (`agents/app/main.py`)
- Streamlit dashboard consuming agent-service mirror endpoints (`dashboards/streamlit_app.py`)
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
                   Streamlit Dashboard
```

## Repository layout

```text
SPECTER/
├── cmd/
│   ├── api/            # Go API server entrypoint
│   ├── collector/      # Go collection + pipeline processing
│   └── worker/         # Worker scaffold
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
├── dashboards/         # Streamlit dashboard
├── scripts/            # Bootstrap and local run helpers
├── justfile            # Developer task runner (dotenv-aware)
├── Makefile            # Build/test task runner (CI friendly)
└── .env.example        # Environment template
```

## Prerequisites

- Go 1.24+
- Python 3.11+
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

Terminal A (Go stack):

```bash
./scripts/run_local.sh
```
or

```bash
make run-local
```

Terminal B (agents service):

```bash
.venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents
```
or

```bash
make run-agents
```

Terminal C (dashboard):

```bash
.venv/bin/streamlit run dashboards/streamlit_app.py
```
or
```bash
make run-dashboard
```

you can also use just instead of make at any point.

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
.venv/bin/python -m pip install pytest streamlit requests
go mod download
```

## Configuration

Environment loading behavior differs by entrypoint:

- Go services load `.env` through `godotenv` in `internal/config/config.go`.
- `just` auto-loads `.env` because `justfile` enables `dotenv-load`.
- `make`, direct `uvicorn`, and direct `streamlit` commands do not auto-parse `.env`; they use exported shell variables and code defaults.

### Core runtime variables

| Variable | Purpose | Default in code |
|---|---|---|
| `API_PORT` | Go API listen port | `8080` |
| `WORKER_CONCURRENCY` | Worker parallelism setting | `4` |
| `COLLECTION_INTERVAL_SECONDS` | Collector tick interval | `60` |
| `DB_DSN` | SQLite DSN | `file:specter.db?_busy_timeout=5000&_journal_mode=WAL` |
| `ABUSEIPDB_API_KEY` | AbuseIPDB provider key | empty |
| `OTX_API_KEY` | OTX provider key | empty |
| `SHODAN_API_KEY` | Shodan provider key | empty |
| `URLHAUS_API_KEY` | URLHaus provider key | empty |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEMO_MODE` | Demo mode toggle | `true` |

### Agents service variables

| Variable | Purpose | Default |
|---|---|---|
| `GO_API_BASE_URL` | Go API base URL used by agents | `http://localhost:8080` |
| `AGENT_REQUEST_TIMEOUT_SECONDS` | HTTP timeout to Go API | `10` |
| `AGENT_MAX_RETRIES` | Retries for agent HTTP calls | `2` |
| `AGENT_MODEL` | Agent model label/config | `gpt-4.1-mini` |
| `RED_AGENT_INTERVAL_SECONDS` | Red agent background interval | `30` |
| `ADVERSARIAL_DB_PATH` | Adversarial mirror sqlite path | `./specter_adversarial.db` |

### Dashboard variable

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_API_BASE_URL` | Agent API base URL used by dashboard requests | `http://localhost:8001` |

Note about `DB_DSN`:

- `.env.example` currently includes a Postgres-style DSN, but the implemented repository uses SQLite (`github.com/mattn/go-sqlite3`).
- For local usage, set `DB_DSN` to the SQLite default shown above unless you intentionally know what you are doing.

Note about `.env.example`:

- Some keys are currently legacy or not consumed by active runtime code paths (`AGENT_SERVICE_PORT`, `LANGCHAIN_API_KEY`, `OPENAI_API_KEY`).
- They are kept for future agent-model integrations and compatibility with earlier planning docs.

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
just check
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

Current report exporter writes a plain text placeholder with `.pdf` extension (see `internal/output/report_exporter.go`).

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

- `scripts/run_local.sh` runs API and worker in background, collector in foreground.
- Network-dependent provider tests may be slow or occasionally skip/pass differently depending on upstream availability.
- `cmd/worker/main.go` is currently a scaffold service.
- `scripts/seed_demo_data.sh` is currently a scaffold.

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

### Dashboard cannot fetch data

Verify both dependencies are up:

- Go API reachable at `http://localhost:8080/health`
- Agents service reachable at `http://localhost:8001/health`

### `make` command does not see `.env`

Use `just` (auto dotenv) or export variables in your shell before `make`.

## License

This project is licensed under the terms in `LICENSE`.
