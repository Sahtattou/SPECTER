# SPECTER Next Sprint Plan — 2026-03-19

This plan is derived from `docs/CHANGE_AUDIT_2026-03-19.md` and synchronized with current `TEAM_TASK_LIST.md` statuses.

## Sprint goal

Close the highest-risk implementation gaps that block demo reliability and final delivery confidence.

---

## Priority 1 — Enforce deduplication in runtime flow

### Why

Dedup hash helpers exist, but duplicate filtering is not explicitly enforced in collector persistence logic.

### Scope

- `cmd/collector/main.go`
- `internal/ingest/dedupe.go`
- `internal/ingest/ingest_test.go` (or add focused tests)

### Deliverables

1. Collector applies dedupe check before `repo.UpsertRecord`.
2. Duplicate behavior is deterministic and documented.
3. Tests cover repeated IOC/source combinations.

### Acceptance criteria

- Repeated same IOC+source records do not produce duplicated persisted outcomes.
- `go test ./...` passes with new dedupe tests.

---

## Priority 2 — Upgrade Go validation/scoring from baseline to parity-oriented rules

### Why

Current Go validation/scoring are functional baseline but not parity-complete with adversarial mirror expectations.

### Scope

- `internal/validation/detector.go`
- `internal/scoring/scorer.go`
- `internal/validation/detector_test.go`
- `internal/scoring/scorer_test.go`

### Deliverables

1. Extended rule checks for common adversarial contradictions.
2. Scoring breakdown fields and richer threshold behavior.
3. Deterministic tests for low/medium/high/critical outcomes.

### Acceptance criteria

- Detector and scorer tests include multi-vector coverage and pass.
- Output stages and fields are consistent with API consumers.

---

## Priority 3 — Implement worker runtime path

### Why

`cmd/worker/main.go` remains scaffold; operational story is incomplete.

### Scope

- `cmd/worker/main.go`
- related storage/API integration points if needed

### Deliverables

1. Worker loop with graceful shutdown (`SIGINT/SIGTERM`).
2. Config-driven concurrency usage.
3. Log visibility for processing lifecycle.

### Acceptance criteria

- Worker starts, processes expected workload path, and shuts down cleanly.
- No panic/deadlock during normal stop/restart.

---

## Priority 4 — Dashboard export actions

### Why

Dashboard currently supports mirror feed/injection but not STIX/PDF export actions.

### Scope

- `dashboards/streamlit_app.py`

### Deliverables

1. STIX export action button (`POST /api/v1/exports/stix`).
2. Report export action button (`POST /api/v1/exports/report`).
3. Artifact path/status surfaced in UI.

### Acceptance criteria

- Export buttons return success/failure feedback with artifact location.
- Manual demo run can trigger both exports from dashboard.

---

## Priority 5 — Contract and E2E confidence tests

### Why

Go API ↔ Agents ↔ Dashboard contracts need explicit guardrails before final demo/submission.

### Scope

- `agents/tests/` (new contract tests)
- Go API endpoint behavior assertions
- optional scripted E2E run verification

### Deliverables

1. Contract tests for request/response schema compatibility.
2. One E2E smoke path (collect -> persist -> mirror/dash visibility -> export).

### Acceptance criteria

- CI/local check command includes these tests.
- Schema drift breaks tests early.

### Status update

- Contract test suite implemented in `agents/tests/test_go_api_contracts.py`.
- Tests now run with a temporary Go API fixture from `agents/tests/conftest.py`.
- Included in `scripts/ci_check.sh` via `pytest -m contract`.

---

## Suggested owner split (example)

- **Go runtime hardening**: Priority 1, 2, 3
- **UI + integration confidence**: Priority 4, 5

Adjust owner names directly in `TEAM_TASK_LIST.md` once assigned.
