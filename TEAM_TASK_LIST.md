# SPECTER Team Task List

Last updated: 2026-03-22
Policy: minimal documentation footprint (README + RUNNING_GUIDE + TEAM_TASK_LIST only)

## Status legend
- `Todo`: not started
- `In Progress`: currently active
- `Done`: implemented/verified

## A) Delivery-critical engineering tasks

1. [In Progress] Expand Go E2E coverage for full flow (collect -> validate -> score -> export)
   - Scope: `internal/*` integration path + scripted orchestration checks
   - Done criteria: deterministic CI-safe test path for end-to-end pipeline behavior

2. [Todo] Add fault-injection resilience tests
   - Scope: provider timeout, HTTP 429/backoff, malformed payload handling
   - Done criteria: pipeline degrades gracefully and recovers without panic/data corruption

3. [In Progress] Wire hosted CI workflow equivalent to local `scripts/ci_check.sh`
   - Scope: GitHub workflow file, branch/PR trigger profile
   - Done criteria: PRs run Go tests + Python tests + contract tests + compile/shell checks

4. [Todo] Validate STIX export interoperability (validator + MISP import)
   - Scope: generated artifacts in `artifacts/stix/`
   - Done criteria: no schema errors on validator/import path

5. [In Progress] Final demo artifact completion
   - Scope: `artifacts/submission_bundle/` screenshots + 2-minute video + final checklist pass
   - Done criteria: complete submission bundle ready without manual patch-up

## B) Runtime hardening and polish

6. [In Progress] Expand dedupe edge-case and load-pattern tests
   - Scope: `internal/ingest/*`, collector duplicate-skip behavior
   - Done criteria: edge-case matrix (empty/malformed/case variants/repeats) covered

7. [In Progress] Extend worker throughput and failure-mode test coverage
   - Scope: `cmd/worker/main.go` runtime behavior under stress/restart
   - Done criteria: clean shutdown/restart and stable processing under synthetic load

8. [Todo] Final report visual polish pass
   - Scope: section/table readability in PDF export while keeping standards-valid output
   - Done criteria: jury-friendly readability with no regression in exporter tests

## C) Documentation maintenance (minimal only)

9. [Done] Prune non-essential docs to minimal set
   - Scope: removed architecture/api/audit/sprint/command-inventory markdown files
   - Done criteria: only `README.md`, `docs/RUNNING_GUIDE.md`, `TEAM_TASK_LIST.md` remain as maintained docs

10. [In Progress] Keep minimal docs synchronized with runtime commands/endpoints/envs
    - Scope: README + RUNNING_GUIDE consistency checks after changes
    - Done criteria: no stale command/endpoint/env references in minimal docs

11. [Done] Bound Blue startup sync burst and make it configurable
    - Scope: `agents/app/adversarial/service.py`, `agents/app/config.py`, `.env.example`
    - Done criteria: startup no longer forces `limit=120` immediate sync by default; sync batch/start behavior controlled by env (`GO_SYNC_BATCH_LIMIT`, `GO_SYNC_ON_STARTUP`)

12. [Done] Remove implicit collector demo seeds from runtime defaults
    - Scope: `internal/config/config.go`, `cmd/collector/main.go`, provider constructors
    - Done criteria: real telemetry collection requires explicit targets (`SHODAN_TARGETS`, `ABUSEIPDB_TARGETS`, `OTX_TARGETS`, `URLHAUS_HOSTS`, `CRTSH_QUERY`), preventing stale example-only refresh loops

## Ownership placeholders
- Go Core: __________________
- Agents/Adversarial: __________________
- Dashboard/Reporting: __________________
- QA/CI: __________________
