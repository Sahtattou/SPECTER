# SPECTER Architecture

This document reflects the current implementation state of SPECTER across Go core services, Python agents, and dashboard.

## Runtime topology

```text
OSINT Providers (Go)
  crt.sh | shodan | urlhaus | abuseipdb | otx
          |
          v
Collector Pipeline (cmd/collector)
  Collect -> Normalize -> Detect -> Score -> Upsert(SQLite)
          |
          v
SQLite Repository (internal/storage)
  threat_records + indices + stage-based queries
          |
          +------------------------------+
          |                              |
          v                              v
Go API (cmd/api, internal/api)     Python Agents (agents/app)
  events/metrics/exports/inject       analysis endpoints + adversarial mirror
          |                              |
          +--------------+---------------+
                         |
                         v
                Streamlit Dashboard
```

## Go core flow

1. `cmd/collector/main.go` loads env config, instantiates providers, and runs a timed collection loop.
2. Each provider emits `models.Threat` records.
3. `internal/ingest/NormalizeThreat` converts raw threats into `models.ThreatRecord`.
4. `internal/validation/Detect` applies baseline quarantine decisions.
5. `internal/scoring/Score` computes score, level, ETA, and stage.
6. `internal/storage.SQLiteRepository.UpsertRecord` persists records to SQLite.

## API surfaces

### Go API (`cmd/api`, `internal/api`)

- `GET /health`
- `GET /api/v1/events`
- `GET /api/v1/events/quarantined`
- `GET /api/v1/metrics/pipeline`
- `POST /api/v1/exports/stix`
- `POST /api/v1/exports/report`
- `POST /api/v1/agents/injections/trigger`

### Agents API (`agents/app/main.py`)

- `GET /health`, `GET /ready`
- `POST /mirror/ingest`
- `POST /mirror/injections/trigger`
- `POST /api/v1/agents/injections/trigger` (alias)
- `GET /mirror/events`
- `GET /mirror/injections`
- `GET /mirror/metrics`
- `POST /agents/blue/analyze`
- `POST /agents/red/inject`
- `POST /agents/run`

## Adversarial mirror subsystem (Python)

Implemented under `agents/app/adversarial/`:

- `queue_manager.py`: shared thread-safe queue (`enqueue/dequeue/size`)
- `blue_agent.py`: enrichment pipeline and source-skipping logic
- `red_agent.py`: interval + manual synthetic injections (4 attack types)
- `detector.py`: ordered detection rules and quarantine/validation stage updates
- `storage.py`: mirror SQLite tables (`mirror_events`, `injections`, `pipeline_runs`)
- `service.py`: orchestration and FastAPI integration surface

## Storage model

Go core persists into `threat_records` (migration: `internal/storage/migrations/001_init.sql`) with fields for:

- IOC identity/provenance
- enrichment and corroboration
- synthetic/poison metadata
- scoring and pipeline stage
- timestamps (`collected_at`, `created_at`, `updated_at`)

Agent mirror persists separate mirror-focused tables in its own SQLite path (`ADVERSARIAL_DB_PATH`).

## Current implementation boundaries

- `cmd/worker/main.go` remains scaffold-level.
- Go detection/scoring are baseline and functional, but not yet full parity with the detailed adversarial-mirror spec.
- STIX export is implemented; report export is functional but currently a text-style placeholder written as `.pdf`.

## Status labels used in docs

- **Implemented now**: observable behavior exists in current runtime paths.
- **Baseline/MVP**: implemented with simplified logic; further hardening or parity work remains.
- **Planned next**: documented target behavior not yet implemented.

## Known gaps

- Go worker orchestration is not implemented yet (`cmd/worker/main.go` scaffold).
- Deduplication helper exists but is not fully enforced in collector persistence flow.
- Go validation/scoring are baseline and should be extended for richer adversarial checks.
- Dashboard still lacks direct STIX/PDF action buttons.
