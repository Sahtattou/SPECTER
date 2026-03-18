# SPECTER Team Task List

## How to use this
- Assign one owner per task.
- Add a deadline to each task.
- Move status from `Todo` -> `In Progress` -> `Review` -> `Done`.
- Do not start integration tasks until prerequisite tasks are complete.

## Suggested team split
- Team A: Go Core (collector, ingest, validation, scoring, API)
- Team B: Python Agents (LangChain + FastAPI service)
- Team C: Frontend + Reporting (dashboard + exports + docs)
- Team D: QA + DevOps (tests, CI, demo stability)

## 1) Go Core Platform

### 1.1 Config and bootstrapping
- [ ] Implement environment parsing and validation in `internal/config/config.go`.
  - Status: In Progress
  - Owner: 
  - Done criteria: `Config` struct exists, but env parsing/validation functions and required-key checks are still missing.
- [ ] Wire startup config into `cmd/api/main.go`, `cmd/worker/main.go`, and `cmd/collector/main.go`.
  - Status: In Progress
  - Owner: 
  - Done criteria: Services currently boot, but still use hardcoded values and no shared config object injection.

### 1.2 Provider hardening
- [ ] Finalize provider interface usage and provider registry in `internal/providers/provider.go`.
  - Status: In Progress
  - Owner: 
  - Done criteria: Provider interface and source clients are implemented, but collector registry/orchestration loop is not wired.
- [ ] Add robust rate limiting, retry/backoff, and timeout handling for all provider clients.
  - Status: In Progress
  - Owner: 
  - Done criteria: Basic timeouts/retries exist per provider, but global 429 backoff/centralized policy is still missing.
- [x] Normalize output fields from all sources to the shared model in `pkg/models/threat.go`.
  - Status: Done
  - Owner: 
  - Done criteria: Providers return `models.ThreatRecord` and support target-type filtering via `Supports`.

### 1.3 Ingestion and dedup
- [x] Implement event normalization in `internal/ingest/normalizer.go`.
  - Status: Done
  - Owner: 
  - Done criteria: IOC type detection and envelope construction are implemented (`DetectType`, `BuildEnvelope`).
- [ ] Implement dedup hash generation and duplicate filtering in `internal/ingest/dedupe.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Duplicate IOC events are skipped or merged deterministically.
- [ ] Add unit tests for edge cases (empty IOC, malformed IOC, mixed case domains).
  - Status: In Progress
  - Owner: 
  - Done criteria: Basic type-detection test exists; edge-case and coverage-focused tests remain.

### 1.4 Storage layer
- [ ] Expand schema in `internal/storage/migrations/001_init.sql` for full pipeline fields.
  - Status: In Progress
  - Owner: 
  - Done criteria: Core fields are present, but advanced fields (e.g., score breakdown/domain age/history/injections) are not yet in Go schema.
- [ ] Implement repository methods in `internal/storage/repository.go`.
  - Status: In Progress
  - Owner: 
  - Done criteria: DB init + single `Save` insert are implemented; CRUD/query methods for events/metrics are still missing.
- [ ] Add DB migration and rollback process.
  - Status: Todo
  - Owner: 
  - Done criteria: New environment can be brought up from zero with one command.

### 1.5 Validation and scoring
- [ ] Implement detection rules in `internal/validation/detector.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Rules quarantine suspicious synthetic/manipulated IOCs correctly.
- [ ] Implement scoring engine in `internal/scoring/scorer.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Composite score, threat level, and days-to-attack are generated.
- [ ] Add test vectors for low/medium/high/critical scoring outcomes.
  - Status: Todo
  - Owner: 
  - Done criteria: Deterministic score tests pass with expected outputs.

## 2) Go API and Worker Services

### 2.1 API routes and handlers
- [ ] Implement router setup in `internal/api/router.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Versioned routes under `/api/v1` are active.
- [ ] Implement event endpoints in `internal/api/handlers_events.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Can fetch scored, quarantined, and recent events.
- [ ] Implement metrics endpoints in `internal/api/handlers_metrics.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Pipeline integrity and run stats returned in JSON.
- [ ] Implement export endpoints in `internal/api/handlers_exports.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: STIX/PDF generation can be triggered via API.

### 2.2 Worker pipeline
- [ ] Implement worker loop in `cmd/worker/main.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Worker consumes events, validates, scores, and persists updates.
- [ ] Add concurrency control and graceful shutdown handling.
  - Status: Todo
  - Owner: 
  - Done criteria: SIGINT/SIGTERM stops processing cleanly.

## 3) Output and Reporting

### 3.1 STIX export
- [ ] Implement STIX bundle generation in `internal/output/stix_exporter.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Valid STIX 2.1 JSON generated with timestamped filenames.
- [ ] Validate output in MISP/STIX validator.
  - Status: Todo
  - Owner: 
  - Done criteria: Export imports cleanly with no schema errors.

### 3.2 PDF report
- [ ] Implement report generation in `internal/output/report_exporter.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: PDF includes executive summary, top threats, quarantine log.
- [ ] Add reusable report templates and consistent styling.
  - Status: Todo
  - Owner: 
  - Done criteria: Report looks presentation-ready for demo jury.

## 4) Python Agents (LangChain)

### 4.1 Agent service foundation
- [x] Expand FastAPI app in `agents/app/main.py` with route structure and health/readiness checks.
  - Status: Done
  - Owner: 
  - Done criteria: Health/readiness endpoints and mirror endpoints are implemented (`/health`, `/ready`, `/mirror/*`, `/api/v1/agents/injections/trigger`).
- [x] Implement settings loader and env validation in `agents/app/config.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Settings are loaded from environment with defaults including mirror controls (`RED_AGENT_INTERVAL_SECONDS`, `ADVERSARIAL_DB_PATH`).
- [x] Define strict request/response schemas in `agents/app/schemas.py`.
  - Status: Done
  - Owner: 
  - Done criteria: All agent IO is validated by Pydantic models.

### 4.2 Go API integration
- [x] Implement HTTP client with retries/timeouts in `agents/app/clients/go_api_client.py`.
  - Status: Done
  - Owner: 
  - Done criteria: All tool calls to Go API are centralized and resilient.
- [x] Integrate event and injection operations directly through `GoAPIClient` and chain protocols.
  - Status: Done
  - Owner: 
  - Done criteria: Chains call `get_recent_events` and `submit_synthetic_event` through client/protocol layer; redundant wrappers removed.

### 4.3 Agent chains
- [x] Implement Blue Analyst chain in `agents/app/chains/blue_analyst_chain.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Produces concise analyst notes and cluster summaries.
- [x] Implement Red Injector chain in `agents/app/chains/red_injector_chain.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Generates realistic synthetic poisoning attempts.
- [x] Implement orchestrator in `agents/app/services/agent_runner.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Can run selected chain by task type and return validated output.

### 4.5 Adversarial mirror subsystem (Blue/Red/Detector)
- [x] Implement shared queue manager in `agents/app/adversarial/queue_manager.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Thread-safe `enqueue`, `dequeue(timeout)`, and `size` are used by Blue/Red/Detector.
- [x] Implement Blue Agent enrichment in `agents/app/adversarial/blue_agent.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Cross-source enrichment, source-skipping, Shodan pacing, and resilient error handling are present.
- [x] Implement Red Agent daemon injector in `agents/app/adversarial/red_agent.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Interval-based + manual injection with four attack types and injection logging to SQLite.
- [x] Implement Detector daemon in `agents/app/adversarial/detector.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Ordered quarantine rules, validated/quarantined stage updates, and injection detection updates are persisted.
- [x] Wire adversarial storage/service in `agents/app/adversarial/storage.py` and `agents/app/adversarial/service.py`.
  - Status: Done
  - Owner: 
  - Done criteria: `mirror_events`, `injections`, `pipeline_runs` persistence and mirror API surfaces are operational.

### 4.4 Agent testing
- [x] Expand tests in `agents/tests/test_blue_agent.py` and `agents/tests/test_red_agent.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Includes success, failure, and schema validation cases.
- [x] Add adversarial mirror integration test in `agents/tests/test_adversarial_mirror.py`.
  - Status: Done
  - Owner: 
  - Done criteria: All four synthetic attack types are injected and detected as caught.

## 5) Dashboard and UX
- [x] Build API-backed dashboard in `dashboards/streamlit_app.py`.
  - Status: Done
  - Owner: 
  - Done criteria: Shows live IOC feed, red-agent activity list, and pipeline metrics from agent mirror APIs.
- [x] Add red-agent activity panel and manual injection trigger button.
  - Status: Done
  - Owner: 
  - Done criteria: Demo can trigger and observe quarantine in real time.
- [ ] Add STIX/PDF export actions from dashboard.
  - Status: Todo
  - Owner: 
  - Done criteria: Buttons call Go API and show artifact path/status.

## 6) QA, Testing, and Reliability
- [ ] Add integration tests for full flow: collect -> ingest -> validate -> score -> export.
  - Status: In Progress
  - Owner: 
  - Done criteria: Go provider tests and basic package tests pass; full collector->worker->export E2E remains pending.
- [ ] Add contract tests between Go API and Python agent service.
  - Status: Todo
  - Owner: 
  - Done criteria: Schema mismatches detected before release.
- [ ] Add fault-injection tests (timeouts, 429s, malformed source payloads).
  - Status: Todo
  - Owner: 
  - Done criteria: Pipeline degrades gracefully and recovers.

## 7) DevOps and Team Workflow
- [ ] Create local one-command startup flow in `scripts/run_local.sh`.
  - Status: In Progress
  - Owner: 
  - Done criteria: Starts API, worker, collector, and instructions for agents/dashboard.
- [ ] Implement realistic seeding in `scripts/seed_demo_data.sh`.
  - Status: Todo
  - Owner: 
  - Done criteria: Demo dataset can be generated quickly for rehearsal.
- [ ] Add CI pipeline (Go tests, Python tests, lint, build checks).
  - Status: Todo
  - Owner: 
  - Done criteria: PRs require green checks before merge.
- [ ] Update `.gitignore` for Python venv, cache, and artifact folders.
  - Status: Todo
  - Owner: 
  - Done criteria: No local artifacts accidentally committed.

## 8) Documentation and Handover
- [ ] Expand API docs in `docs/api.md` with endpoint request/response examples.
  - Status: Todo
  - Owner: 
  - Done criteria: Team can integrate from docs alone.
- [ ] Expand architecture doc in `docs/architecture.md` with data flow diagram.
  - Status: Todo
  - Owner: 
  - Done criteria: New team member can understand the stack in under 15 minutes.
- [ ] Update `README.md` with setup, run commands, and troubleshooting.
  - Status: Todo
  - Owner: 
  - Done criteria: Fresh clone can run project by following README only.

## 9) Demo and Submission Readiness
- [ ] Finalize demo script and speaking flow.
  - Status: Todo
  - Owner: 
  - Done criteria: 10-minute demo fits time and includes live poisoning catch moment.
- [ ] Prepare backup offline demo data in case of API rate-limit/network issues.
  - Status: Todo
  - Owner: 
  - Done criteria: Demo still works without live internet.
- [ ] Produce final artifacts bundle: STIX sample, PDF sample, screenshots, 2-minute video.
  - Status: Todo
  - Owner: 
  - Done criteria: All submission deliverables complete and reviewed.

## Critical path (must finish first)
- [ ] Providers stable and normalized output
- [ ] Ingestion + dedup + storage fully functional
- [ ] Validation + scoring fully functional
- [ ] API endpoints for events/metrics working
- [x] Dashboard wired to API
- [x] Red injection and quarantine visible in live demo

## Weekly checkpoints
- [ ] Checkpoint 1: Data ingestion and storage complete
- [ ] Checkpoint 2: Validation/scoring + API complete
- [x] Checkpoint 3: Agents integrated + dashboard complete
- [ ] Checkpoint 4: Demo rehearsal + bug fixes + final docs
