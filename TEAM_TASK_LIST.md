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
  - Status: Todo
  - Owner: 
  - Done criteria: Required env vars validated at startup with clear error messages.
- [ ] Wire startup config into `cmd/api/main.go`, `cmd/worker/main.go`, and `cmd/collector/main.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: All services boot with config object; no hardcoded values.

### 1.2 Provider hardening
- [ ] Finalize provider interface usage and provider registry in `internal/providers/provider.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Collector loops through providers consistently.
- [ ] Add robust rate limiting, retry/backoff, and timeout handling for all provider clients.
  - Status: Todo
  - Owner: 
  - Done criteria: 429 and transient network failures are retried safely.
- [ ] Normalize output fields from all sources to the shared model in `pkg/models/threat.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: All providers emit consistent IOC records.

### 1.3 Ingestion and dedup
- [ ] Implement event normalization in `internal/ingest/normalizer.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Input provider events produce canonical event objects.
- [ ] Implement dedup hash generation and duplicate filtering in `internal/ingest/dedupe.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: Duplicate IOC events are skipped or merged deterministically.
- [ ] Add unit tests for edge cases (empty IOC, malformed IOC, mixed case domains).
  - Status: Todo
  - Owner: 
  - Done criteria: Tests cover at least 90% of ingest package logic.

### 1.4 Storage layer
- [ ] Expand schema in `internal/storage/migrations/001_init.sql` for full pipeline fields.
  - Status: Todo
  - Owner: 
  - Done criteria: Schema supports provenance, validation, scoring, and synthetic flags.
- [ ] Implement repository methods in `internal/storage/repository.go`.
  - Status: Todo
  - Owner: 
  - Done criteria: CRUD for events, queries for recent/scored/quarantined metrics.
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
- [ ] Expand FastAPI app in `agents/app/main.py` with route structure and health/readiness checks.
  - Status: Todo
  - Owner: 
  - Done criteria: Agent service exposes stable endpoints and OpenAPI docs.
- [ ] Implement settings loader and env validation in `agents/app/config.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Missing critical keys fail fast with clear messages.
- [ ] Define strict request/response schemas in `agents/app/schemas.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: All agent IO is validated by Pydantic models.

### 4.2 Go API integration
- [ ] Implement HTTP client with retries/timeouts in `agents/app/clients/go_api_client.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: All tool calls to Go API are centralized and resilient.
- [ ] Implement event and injection tools in `agents/app/tools/event_tools.py` and `agents/app/tools/injection_tools.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Tools can read events and submit synthetic injections.

### 4.3 Agent chains
- [ ] Implement Blue Analyst chain in `agents/app/chains/blue_analyst_chain.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Produces concise analyst notes and cluster summaries.
- [ ] Implement Red Injector chain in `agents/app/chains/red_injector_chain.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Generates realistic synthetic poisoning attempts.
- [ ] Implement orchestrator in `agents/app/services/agent_runner.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Can run selected chain by task type and return validated output.

### 4.4 Agent testing
- [ ] Expand tests in `agents/tests/test_blue_agent.py` and `agents/tests/test_red_agent.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Includes success, failure, and schema validation cases.

## 5) Dashboard and UX
- [ ] Build API-backed dashboard in `dashboards/streamlit_app.py`.
  - Status: Todo
  - Owner: 
  - Done criteria: Shows live feed, threat distribution, and pipeline metrics.
- [ ] Add red-agent activity panel and manual injection trigger button.
  - Status: Todo
  - Owner: 
  - Done criteria: Demo can trigger and observe quarantine in real time.
- [ ] Add STIX/PDF export actions from dashboard.
  - Status: Todo
  - Owner: 
  - Done criteria: Buttons call Go API and show artifact path/status.

## 6) QA, Testing, and Reliability
- [ ] Add integration tests for full flow: collect -> ingest -> validate -> score -> export.
  - Status: Todo
  - Owner: 
  - Done criteria: End-to-end tests pass in local and CI environments.
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
- [ ] Dashboard wired to API
- [ ] Red injection and quarantine visible in live demo

## Weekly checkpoints
- [ ] Checkpoint 1: Data ingestion and storage complete
- [ ] Checkpoint 2: Validation/scoring + API complete
- [ ] Checkpoint 3: Agents integrated + dashboard complete
- [ ] Checkpoint 4: Demo rehearsal + bug fixes + final docs
