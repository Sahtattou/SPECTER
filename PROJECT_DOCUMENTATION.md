# SPECTER — Comprehensive Project Documentation

Last updated: 2026-03-24

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Core Data Models](#4-core-data-models)
5. [End-to-End Pipeline Flow](#5-end-to-end-pipeline-flow)
6. [Go Services](#6-go-services)
7. [Python Agents Service](#7-python-agents-service)
8. [API Reference](#8-api-reference)
9. [Exports and Artifacts](#9-exports-and-artifacts)
10. [Frontend and Dashboard Behavior](#10-frontend-and-dashboard-behavior)
11. [Configuration Reference](#11-configuration-reference)
12. [Local Development and Operations](#12-local-development-and-operations)
13. [Testing and Quality Gates](#13-testing-and-quality-gates)
14. [Troubleshooting Guide](#14-troubleshooting-guide)
15. [Security, Ethics, and Operational Guardrails](#15-security-ethics-and-operational-guardrails)
16. [Known Limitations](#16-known-limitations)
17. [Roadmap and Open Work](#17-roadmap-and-open-work)
18. [File-Level Reference Map](#18-file-level-reference-map)

---

## 1) Project Overview

SPECTER is an operational Threat Intelligence prototype that transforms public OSINT indicators into analyst-ready intelligence.

It implements a complete flow:

**Collect → Normalize → Detect → Score → Persist → Serve via APIs → Mirror/Adversarial Evaluation → Export (STIX/PDF) → Dashboard consumption.**

Primary goals:

- Collect from multiple OSINT sources.
- Preserve source traceability and evidence.
- Reduce noise via normalization, dedupe, and validation rules.
- Produce structured, actionable outputs for SOC workflows.
- Evaluate poisoning resilience via red/blue adversarial mirror.

Primary technology stack:

- **Go**: collector, worker, API, scoring, validation, storage.
- **Python (FastAPI)**: agents service, adversarial mirror, blue/red chains, mirror exports.
- **React + TypeScript + Tauri**: desktop dashboard.
- **SQLite**: persistence backend for Go pipeline and mirror service.

---

## 2) System Architecture

```text
OSINT Providers (Go)
  crt.sh, Shodan, URLHaus, AbuseIPDB, OTX
          |
          v
Collector + Normalize + Detect + Score (Go)
  cmd/collector -> internal/ingest -> internal/validation -> internal/scoring
          |
          v
Persistence (SQLite)
  internal/storage (threat_records)
          |
          +------------------------------+
          |                              |
          v                              v
Go REST API                        Python Agent Service
  /api/v1/events, metrics,           /agents/*, /mirror/*
  exports, injections                syncs with Go API
          |                              |
          +--------------+---------------+
                         |
                         v
               Tauri + React Desktop Dashboard
```

Key design decision:

- Dashboard and mirror exports are aligned through a **single agents snapshot contract** (`GET /mirror/dashboard`) to reduce cross-endpoint drift.

---

## 3) Repository Structure

```text
SPECTER/
├── cmd/
│   ├── api/            # Go API entrypoint
│   ├── collector/      # Go collector pipeline runtime
│   └── worker/         # Go scoring worker runtime
├── internal/
│   ├── api/            # Go HTTP router + handlers
│   ├── config/         # Go runtime configuration loader
│   ├── ingest/         # Threat normalization + dedupe helpers
│   ├── output/         # STIX and PDF report exporters
│   ├── providers/      # OSINT provider clients + error classification
│   ├── scoring/        # Threat scoring logic
│   ├── storage/        # SQLite repository + migration
│   └── validation/     # Detection / quarantine rules
├── pkg/models/         # Shared Go domain models
├── agents/
│   └── app/
│       ├── adversarial/   # mirror service + red/blue/detector/storage
│       ├── chains/        # blue/red chain entrypoints
│       ├── clients/       # Go API HTTP client
│       ├── config.py      # agents env config
│       ├── exports.py     # mirror snapshot exports
│       ├── main.py        # FastAPI app and routes
│       └── schemas.py     # request/response schemas
├── frontend/           # React + TypeScript + Tauri desktop app
├── scripts/            # bootstrap, local orchestration, smoke/demo/bundle helpers
├── docs/
│   └── RUNNING_GUIDE.md
├── README.md
├── TEAM_TASK_LIST.md
└── PROJECT_DOCUMENTATION.md
```

---

## 4) Core Data Models

### 4.1 Go models (`pkg/models/threat.go`)

#### `Threat` (raw ingest model)

Contains raw provider fields:

- `ioc_value`, `ioc_type`
- `source_name`, `source_url`, `source_query`
- `raw_evidence`, `collected_at`
- optional enrichment data: `open_ports`, `asn`, `corroboration`
- adversarial flags: `is_synthetic`, `poison_attack_type`

#### `ThreatRecord` (normalized/persisted model)

Contains normalized + computed fields:

- identity: `event_id`
- source + evidence fields
- scoring fields: `composite_score`, `threat_level`, `days_to_attack`
- validation fields: `poison_detected`, `detection_rule`, `pipeline_stage`
- lifecycle: `created_at`, `updated_at`

### 4.2 Agents mirror model (`agents/app/adversarial/models.py`)

#### `IOCEnvelope`

Mirror-side event container with:

- `ioc_uuid`, `raw_value`, `ioc_type`
- source/evidence fields
- pipeline state: `pipeline_stage`, synthetic and poison fields
- enrichment/scoring metadata: `corroboration_count`, `domain_age_days`, `open_ports`, `asn`, `composite_score`, `score_breakdown`, `days_to_attack_estimate`, `threat_level`

---

## 5) End-to-End Pipeline Flow

### 5.1 Go ingest and processing

1. Providers collect raw threats.
2. Collector normalizes threats (`NormalizeThreat`).
3. Collector deduplicates candidate records (`DedupeHash` + in-memory cycle dedupe).
4. Collector validates poisoning/noise rules (`validation.Detect`).
5. Collector scores threat priority (`scoring.Score`).
6. Repository persists with upsert semantics (`UpsertRecord`).

Main code path:

- `cmd/collector/main.go`
- `internal/ingest/normalizer.go`
- `internal/ingest/dedupe.go`
- `internal/validation/detector.go`
- `internal/scoring/scorer.go`
- `internal/storage/repository.go`

### 5.2 Worker scoring pass

Worker periodically:

- loads `validated` records,
- re-scores concurrently,
- writes back to storage.

Main code:

- `cmd/worker/main.go`

### 5.3 Agents mirror flow

Mirror service starts:

- detector thread,
- red agent thread,
- Go-sync thread.

For real event ingest (`/mirror/ingest` or Go sync):

1. Build `IOCEnvelope`.
2. Blue agent enriches context.
3. Preserve upstream scoring/detection fields when provided.
4. Persist to mirror DB + enqueue for detector.

For synthetic injection:

1. Red agent generates attack IOC.
2. Logs injection metadata.
3. Enqueues envelope.
4. Detector evaluates, sets `poison_detected` and `detection_rule`, and updates injection outcome by `ioc_uuid`.

Main code:

- `agents/app/adversarial/service.py`
- `agents/app/adversarial/red_agent.py`
- `agents/app/adversarial/blue_agent.py`
- `agents/app/adversarial/detector.py`
- `agents/app/adversarial/storage.py`

---

## 6) Go Services

### 6.1 API service (`cmd/api/main.go`)

- Loads config.
- Opens SQLite repository.
- Registers router with CORS.
- Serves HTTP on `API_PORT` (default `8080`).

Router and handlers:

- `internal/api/router.go`
- `internal/api/handlers_events.go`
- `internal/api/handlers_metrics.go`
- `internal/api/handlers_exports.go`

### 6.2 Collector (`cmd/collector/main.go`)

Responsibilities:

- Build provider list from env configuration.
- Run collection loop on interval.
- Classify provider failures and apply cooldown/suppression.
- Normalize, detect, score, persist.

Notable resilience behavior:

- `429` / rate limits => temporary disable window.
- auth/plan restrictions => long suppression window.
- transient failures => exponential-ish bounded backoff.

### 6.3 Worker (`cmd/worker/main.go`)

Responsibilities:

- Concurrently process validated records.
- Re-score and persist.
- Graceful shutdown on SIGINT/SIGTERM.

---

## 7) Python Agents Service

### 7.1 Service entrypoint (`agents/app/main.py`)

Responsibilities:

- FastAPI app initialization.
- CORS setup.
- Adversarial service lifecycle startup.
- Mirror + chain endpoint exposure.

### 7.2 Adversarial mirror service (`agents/app/adversarial/service.py`)

Responsibilities:

- Manage shared queue, red/blue/detector components.
- Ingest real IOCs and sync Go events.
- Calculate mirror metrics and dashboard snapshot.
- Enforce auto-red guardrails (`red_max_ratio`, `min_real_events_before_auto_red`).

### 7.3 Blue agent (`agents/app/adversarial/blue_agent.py`)

Responsibilities:

- URL host extraction + normalization.
- Source-aware enrichment calls (abuseipdb/shodan/whois/urlhaus/otx).
- Corroboration count updates.
- Enrichment evidence attachment.

### 7.4 Red agent (`agents/app/adversarial/red_agent.py`)

Supported attack types:

- `REPUTATION_LAUNDERING`
- `GHOST_DOMAIN`
- `TTP_MISMATCH`
- `TIMESTAMP_MANIPULATION`

Adaptive features:

- Uses recent injection outcomes (hits/misses/unresolved) for weighted attack selection.
- Deterministic RNG injection supported for testability.
- Logs strategy metadata under `raw_evidence.red_strategy`.

### 7.5 Detector (`agents/app/adversarial/detector.py`)

Rules:

- `SINGLE_SOURCE_FRESH_DOMAIN`
- `TTP_BANNER_MISMATCH`
- `SUSPICIOUS_TIMESTAMP`

Outcome behavior:

- Quarantine or validate event.
- Persist event state.
- If synthetic, update linked injection detection record.

### 7.6 Mirror storage (`agents/app/adversarial/storage.py`)

Tables:

- `mirror_events`
- `injections`
- `pipeline_runs`

Provides:

- event/injection queries,
- metrics aggregation,
- per-source freshness,
- pipeline run tracking.

---

## 8) API Reference

## 8.1 Go API (default `http://localhost:8080`)

Defined in `internal/api/router.go`.

### `GET /health`

- Purpose: service liveness.
- Handler: `handleHealth`.

### `GET /api/v1/events`

- Purpose: list all events or by stage.
- Query:
  - `stage` (optional)
  - `limit` (optional)
- Handler: `handleEvents`.

### `GET /api/v1/events/quarantined`

- Purpose: list quarantined events.
- Handler: `handleQuarantined`.

### `GET /api/v1/metrics/pipeline`

- Purpose: pipeline metrics and freshness telemetry.
- Includes:
  - `total_events`, `quarantined_count`, `scored_count`
  - `last_collected_at`, `last_updated_at`
  - `freshness_age_seconds`, `distinct_sources`, `source_freshness_age_seconds`
- Handler: `handleMetrics`.

### `POST /api/v1/exports/stix`

- Purpose: generate STIX export from scored records.
- Handler: `handleExportSTIX`.

### `POST /api/v1/exports/report`

- Purpose: generate PDF report export from all records.
- Handler: `handleExportReport`.

### `POST /api/v1/agents/injections/trigger`

- Purpose: submit manual synthetic event payload into Go pipeline.
- Handler: `handleInjectionTrigger`.

## 8.2 Agents API (default `http://localhost:8001`)

Defined in `agents/app/main.py`.

### Health and readiness

- `GET /health`
- `GET /ready`

### Mirror endpoints

- `POST /mirror/ingest`
- `POST /mirror/injections/trigger`
- `POST /api/v1/agents/injections/trigger` (alias)
- `GET /mirror/events`
- `GET /mirror/injections`
- `GET /mirror/metrics`
- `GET /mirror/dashboard`

### Mirror exports

- `POST /mirror/exports/stix`
- `POST /mirror/exports/report`

### Chain-style agent endpoints

- `POST /agents/blue/analyze`
- `POST /agents/red/inject`
- `POST /agents/run`

---

## 9) Exports and Artifacts

## 9.1 Go exports (`internal/output/*`)

- STIX: `internal/output/stix_exporter.go`
- Report PDF: `internal/output/report_exporter.go`

Output directories:

- `artifacts/stix/`
- `artifacts/reports/`

## 9.2 Mirror snapshot exports (`agents/app/exports.py`)

Mirror-specific exports are generated from the same snapshot basis used by dashboard rendering.

Snapshot metadata included:

- `snapshot_generated_at`
- derived `snapshot_id`
- content hash basis metadata

Endpoints:

- `POST /mirror/exports/stix`
- `POST /mirror/exports/report`

---

## 10) Frontend and Dashboard Behavior

Main client hook:

- `frontend/src/hooks/useDashboardData.ts`

Behavior:

- Polls mirror snapshot every 10 seconds by default.
- Uses `GET /mirror/dashboard` as primary source for metrics/events/injections.
- Triggers mirror injection and export endpoints.

API client:

- `frontend/src/api/client.ts`

Type contracts:

- `frontend/src/types/api.ts`

Key UI consistency rule:

- Pipeline overview and live feed are sourced from the same atomic snapshot to minimize drift.

---

## 11) Configuration Reference

## 11.1 Go config (`internal/config/config.go`)

Important variables:

- Ports/runtime: `API_PORT`, `WORKER_CONCURRENCY`, `COLLECTION_INTERVAL_SECONDS`
- DB: `DB_DSN`
- provider keys/targets: `SHODAN_API_KEY`, `ABUSEIPDB_API_KEY`, `OTX_API_KEY`, `URLHAUS_API_KEY`, `CRTSH_QUERY`, `*_TARGETS`
- provider switches: `ENABLE_SHODAN`, `ENABLE_ABUSEIPDB`, `ENABLE_OTX`, `ENABLE_URLHAUS`, `ENABLE_CRTSH`

## 11.2 Agents config (`agents/app/config.py`)

Important variables:

- API and transport: `GO_API_BASE_URL`, `AGENT_REQUEST_TIMEOUT_SECONDS`, `AGENT_MAX_RETRIES`
- CORS: `AGENT_ALLOWED_ORIGINS`
- red/blue control: `RED_AGENT_INTERVAL_SECONDS`, `RED_MAX_RATIO`, `MIN_REAL_EVENTS_BEFORE_AUTO_RED`
- Go sync controls: `GO_SYNC_INTERVAL_SECONDS`, `GO_SYNC_BATCH_LIMIT`, `GO_SYNC_ON_STARTUP`
- storage: `ADVERSARIAL_DB_PATH`

## 11.3 Frontend config

- `VITE_AGENT_API_BASE_URL`
- `VITE_GO_API_BASE_URL`

---

## 12) Local Development and Operations

## 12.1 Bootstrap

```bash
./scripts/bootstrap.sh
```

## 12.2 Start all local services

```bash
./scripts/run_local.sh start
```

Control commands:

```bash
./scripts/run_local.sh status
./scripts/run_local.sh logs
./scripts/run_local.sh stop
./scripts/run_local.sh restart
```

## 12.3 Run individual service paths

Go:

```bash
go run ./cmd/api
go run ./cmd/worker
go run ./cmd/collector
```

Agents:

```bash
.venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents
```

Dashboard:

```bash
npm run tauri dev --prefix frontend
```

## 12.4 Task runners

- `Makefile` for CI-style and conventional targets.
- `justfile` for local convenience with `.env` auto-load.

---

## 13) Testing and Quality Gates

## 13.1 Go tests

```bash
go test ./...
```

## 13.2 Python tests

```bash
.venv/bin/python -m pytest agents/tests
```

## 13.3 Local CI-equivalent profile

```bash
make ci-check
# or
just ci-check
```

`scripts/ci_check.sh` runs:

- Go tests,
- Python tests,
- contract-only tests,
- Python compile checks,
- shell script syntax checks.

---

## 14) Troubleshooting Guide

Use `docs/RUNNING_GUIDE.md` as primary operations runbook. Key issues:

1. **No real telemetry**
   - Verify provider targets and keys (`*_TARGETS`, `*_API_KEY`).
2. **Provider noise (429 / membership errors)**
   - Use `ENABLE_ABUSEIPDB=false` / `ENABLE_SHODAN=false` and restart.
3. **Dashboard fetch errors**
   - Confirm Go and Agents health endpoints and CORS origins.
4. **Stale/flat totals**
   - Compare mirror snapshot metrics (`pipeline_run_total`) with Go freshness endpoint.
5. **Partial local startup**
   - Re-run bootstrap and restart local orchestrator.

---

## 15) Security, Ethics, and Operational Guardrails

- Uses public OSINT providers and configurable test targets.
- Adversarial simulation is explicitly marked synthetic (`is_synthetic`).
- Auto-red guardrails reduce synthetic skew:
  - ratio gating (`RED_MAX_RATIO`)
  - baseline real-event threshold (`MIN_REAL_EVENTS_BEFORE_AUTO_RED`)
- Provider failure handling includes suppression/cooldown to avoid noisy loops.

---

## 16) Known Limitations

1. SQLite-first persistence is ideal for prototyping but not horizontal scale.
2. External provider quotas and account restrictions can reduce live collection quality.
3. Some roadmap tasks remain open (fault-injection resilience tests, STIX interoperability validation, hosted CI completion).

Reference:

- `TEAM_TASK_LIST.md`

---

## 17) Roadmap and Open Work

Current tracked priorities include:

- Expand deterministic Go E2E coverage.
- Add fault-injection resilience tests.
- Complete hosted CI wiring equivalent to local `ci-check`.
- Validate STIX interoperability with external validators/import paths.
- Finalize demo artifacts (screenshots/video/checklist).

Source:

- `TEAM_TASK_LIST.md`

---

## 18) File-Level Reference Map

### Go runtime and pipeline

- `cmd/api/main.go`
- `cmd/collector/main.go`
- `cmd/worker/main.go`
- `internal/config/config.go`
- `internal/ingest/normalizer.go`
- `internal/ingest/dedupe.go`
- `internal/validation/detector.go`
- `internal/scoring/scorer.go`
- `internal/storage/repository.go`
- `internal/storage/migrations/001_init.sql`

### Go API and exports

- `internal/api/router.go`
- `internal/api/handlers_events.go`
- `internal/api/handlers_metrics.go`
- `internal/api/handlers_exports.go`
- `internal/output/stix_exporter.go`
- `internal/output/report_exporter.go`

### Agents/adversarial

- `agents/app/main.py`
- `agents/app/config.py`
- `agents/app/schemas.py`
- `agents/app/clients/go_api_client.py`
- `agents/app/exports.py`
- `agents/app/adversarial/service.py`
- `agents/app/adversarial/storage.py`
- `agents/app/adversarial/detector.py`
- `agents/app/adversarial/blue_agent.py`
- `agents/app/adversarial/red_agent.py`
- `agents/app/adversarial/models.py`

### Frontend

- `frontend/src/hooks/useDashboardData.ts`
- `frontend/src/api/client.ts`
- `frontend/src/types/api.ts`

### Scripts and operations

- `scripts/bootstrap.sh`
- `scripts/run_local.sh`
- `scripts/ci_check.sh`
- `scripts/seed_demo_data.sh`
- `scripts/agent_smoke.sh`
- `scripts/rehearse_demo.sh`
- `scripts/load_offline_snapshot.sh`
- `scripts/create_artifact_bundle.sh`

### Main docs

- `README.md`
- `docs/RUNNING_GUIDE.md`
- `TEAM_TASK_LIST.md`
- `PROJECT_DOCUMENTATION.md`

---

## Quick Start (One Screen)

```bash
./scripts/bootstrap.sh
./scripts/run_local.sh start
curl -s http://localhost:8080/health
curl -s http://localhost:8001/health
.venv/bin/python -m pytest agents/tests
go test ./...
```

---

This document is the full technical reference. Use `README.md` for fast onboarding and `docs/RUNNING_GUIDE.md` for operational runbooks.
