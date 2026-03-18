# SPECTER — Project Plan
## Self-Poisoning Early-warning Cyber Threat Engine & Reporter

---

## What you are building and why it matters

You are building SPECTER, a functional Threat Intelligence (TI) prototype for a cybersecurity hackathon called **Cyber Horizon 2.0 — Open Threat Intelligence Challenge (OTIC)**. The challenge requires a working prototype that transforms raw, publicly available internet data (OSINT) into structured, actionable intelligence that a Security Operations Center (SOC) team can use.

The hackathon judges will be cybersecurity professionals. They have seen dozens of student projects. Most of those projects are dashboards that pull data from an API and display it. SPECTER is fundamentally different. It does something no other student prototype does: it attacks itself.

SPECTER runs two agents simultaneously on the same pipeline. The Blue Collector processes real threat signals from public internet sources. The Red Injector — running in a background thread — quietly plants fake, poisoned threat indicators into the same processing queue. The pipeline must catch those injections before they reach the final report. Every catch (and every miss) is logged, scored, and displayed live.

The live demo moment — watching the Red Agent fire a poisoned IOC and the system catch it in real time — is the presentation centerpiece. Build toward that moment. Every architectural decision should make that moment more dramatic, more credible, and more technically impressive.

---

## Hackathon context

**Event:** Cyber Horizon 2.0 — Open Threat Intelligence Challenge
**Challenge type:** Technical prototype
**Team size:** 2–4 members
**Phase 1 deadline:** 15 March 2026
**Deliverables:** Working prototype demo, report, presentation, video (max 2 min)

**Scoring rubric (total: 20 points)**

| Criterion | Points | What the judge is looking for |
|---|---|---|
| Prototype functionality & stability | 5 | Does it run without crashing? Does it do what you claim? |
| TI pipeline implementation | 4 | Are all pipeline stages present and connected? |
| Reporting & usability | 3 | Can a SOC analyst actually use the output? |
| Presentation clarity | 3 | Is the demo convincing and understandable? |
| Compliance with rules | 2 | Only public OSINT, no targeting of real people/orgs |
| Originality | 1 | Is this genuinely novel? |
| SOC integration readiness (bonus) | 1 | Does output plug into real SOC tooling? |
| Ethical OSINT handling (bonus) | 1 | Is all data sourced ethically and legally? |

**Critical rules you must never violate:**
- Only use publicly available OSINT data sources
- Never target real individuals or specific real organizations
- The prototype must actually run — concept-only gets disqualified
- All API keys must be free-tier (no paid services)

---

## The core idea in plain language

Traditional threat intelligence tools are reactive. They collect indicators of compromise (IOCs — things like malicious IP addresses, suspicious domains, and dangerous URLs) after attacks happen. They are newspapers: they tell you what happened yesterday.

SPECTER adds two things that make it a weather forecast instead:

**1. Pre-attack detection.** By monitoring Certificate Transparency logs, newly registered domains, and infrastructure fingerprints on Shodan, SPECTER finds attacker infrastructure while it is being staged — before it goes live. A domain registered 48 hours ago with a lookalike certificate for a major bank, hosted on an IP with port 50050 open (a known Cobalt Strike C2 port), is suspicious now — not after it sends phishing emails.

**2. Self-adversarial validation.** SPECTER's Red Injector deliberately tries to corrupt its own pipeline by injecting synthetic poisoned IOCs. If the pipeline catches them, every IOC in the final report carries an implicit guarantee: it survived an adversarial test. This is a form of automated pipeline integrity validation that no comparable open-source tool does.

---

## Key terminology (read this before touching the code)

**IOC (Indicator of Compromise):** A piece of data that suggests malicious activity. Examples: an IP address known to host malware, a domain registered to look like a bank, a URL hosting a phishing kit.

**OSINT (Open-Source Intelligence):** Intelligence gathered from publicly available sources. In this context: public APIs, certificate transparency logs, community-submitted threat feeds.

**SOC (Security Operations Center):** The team inside an organization that monitors for and responds to cyber threats. They are the end consumer of SPECTER's output.

**STIX 2.1:** A standardized JSON format for sharing threat intelligence. Industry standard. A STIX bundle can be imported directly into tools like MISP, Splunk, or any modern SIEM. This is how you earn the SOC integration readiness bonus point.

**MISP:** A threat intelligence platform widely used by SOC teams. If your STIX bundle imports cleanly into MISP, your SOC integration story is credible.

**C2 (Command and Control):** Infrastructure that attackers use to control malware on victim machines. Common C2 frameworks used by real attackers include Cobalt Strike (port 50050), Havoc (port 40056), and Sliver (port 8888). Finding these ports open on fresh, unregistered IP addresses is a strong pre-attack signal.

**Kill chain:** A model of the stages of a cyberattack (reconnaissance → resource development → initial access → etc.). SPECTER maps IOCs to kill chain stages based on their characteristics.

**Provenance:** The complete traceable history of where a piece of data came from — which API, which query, at what time, with what raw response. This is what makes intelligence "traceable" rather than just "collected."

**Corroboration:** An IOC that appears in multiple independent sources is more trustworthy than one that appears in only one. Cross-source corroboration is one of the five scoring dimensions.

**Days-to-Attack estimate:** SPECTER's signature output metric. Based on the characteristics of the IOC (how fresh the infrastructure is, what ports are open, what the cert pattern looks like), SPECTER estimates how many days until this infrastructure likely goes active. This is heuristic — not a trained ML model — and must be disclosed as such in the report.

---

## Architecture overview

SPECTER uses a hybrid architecture:
- Go handles high-throughput collection, ingestion, scoring, and API serving.
- Python handles adversarial and analyst-assist agents using LangChain.

SPECTER still has 6 layers, but responsibilities are split by language.

```
LAYER 1 — Go Collection
    Providers query public OSINT APIs on schedules
    (crt.sh, Shodan, URLhaus, AbuseIPDB, OTX)
         ↓
LAYER 2 — Go Ingestion + Provenance
    Normalize IOCs into canonical ThreatEvent model
    Add UUID, source trace, timestamps, dedup hash
    Persist to PostgreSQL/SQLite and publish to queue
         ↓
LAYER 3 — Go Validation + Scoring
    Rule detector validates or quarantines events
    Score clean events (0-100) and assign threat level
    Expose REST API for dashboard/reporting
         ↓
LAYER 4 — Python Agent Service (LangChain)
    Blue Analyst Agent: summarize and explain suspicious IOC clusters
    Red Injector Agent: generate synthetic poisoning attempts
    Optional Triage Agent: produce SOC-ready action recommendations
         ↓
LAYER 5 — Go/Python Output Generation
    STIX 2.1 bundle export, PDF report generation, timeline artifacts
         ↓
LAYER 6 — SOC Consumption
    Dashboard + API + downloadable artifacts for SIEM/MISP workflows
```

---

## Data sources

All free tier. No payment required. Register for API keys where indicated.

### crt.sh — Certificate Transparency logs
- **What it is:** A public database of every SSL/TLS certificate ever issued. When an attacker registers a lookalike domain and gets a cert for it, it appears here within minutes.
- **Why it matters:** Certificates are issued days before phishing campaigns launch. This is SPECTER's earliest possible signal.
- **API endpoint:** `https://crt.sh/?q={pattern}&output=json`
- **No API key required**
- **Query patterns to use:**
  - `%.secure-login`
  - `%.account-verify`
  - `%.paypal-` (lookalike phishing prep)
  - `%.update-billing`
  - `%.support-helpdesk`
- **Fields to extract:** `name_value` (the domain), `not_before` (cert issuance date), `issuer_name`, `id`
- **Rate limit:** Be respectful. Add `time.sleep(2)` between queries.

### Shodan — Internet-wide port scanning
- **What it is:** A search engine for internet-connected devices. It continuously scans the entire internet and records what ports are open and what banners services are serving.
- **Why it matters:** Attacker C2 infrastructure has distinctive port/banner fingerprints. A fresh IP with port 50050 open and a Cobalt Strike default certificate is a very strong signal.
- **API endpoint:** `https://api.shodan.io/shodan/host/search?key={key}&query={query}`
- **Requires free API key:** Register at shodan.io
- **Queries to run:**
  - `port:50050` (Cobalt Strike)
  - `port:40056` (Havoc C2)
  - `ssl.cert.subject.cn:*.xyz port:443` (suspicious wildcard certs on cheap TLDs)
- **Fields to extract:** `ip_str`, `ports`, `hostnames`, `org`, `asn`, `data[n].banner`, `last_update`
- **Rate limit:** 1 request/second on free tier. Enforce strictly with `time.sleep(1)`.

### URLhaus — Malicious URL community feed
- **What it is:** A community-driven database of URLs currently hosting malware or being used in phishing campaigns. Run by abuse.ch.
- **Why it matters:** Provides ground-truth malicious IOCs to cross-reference against. If your cert pipeline finds a domain that URLhaus also flagged, confidence doubles.
- **API endpoint:** `https://urlhaus-api.abuse.ch/v1/urls/recent/` (POST request)
- **No API key required**
- **Request body:** `{"limit": 100}`
- **Fields to extract:** `url`, `url_status` (online/offline), `threat` (malware_download/phishing etc.), `tags`, `date_added`

### AbuseIPDB — IP reputation database
- **What it is:** A community database of IP addresses reported for abusive behavior (spam, scanning, attacks). Each IP has a confidence score 0–100.
- **Why it matters:** Provides reputation context for IPs found by Shodan. Also used as an enrichment source for cross-corroboration.
- **API endpoint:** `https://api.abuseipdb.com/api/v2/blacklist`
- **Requires free API key:** Register at abuseipdb.com
- **Headers:** `Key: {key}`, `Accept: application/json`
- **Params:** `confidenceMinimum=80&limit=100`
- **Fields to extract:** `ipAddress`, `abuseConfidenceScore`, `lastReportedAt`, `countryCode`, `totalReports`

### OTX AlienVault — Community threat intelligence pulses
- **What it is:** A platform where security researchers share threat intelligence "pulses" — curated collections of IOCs related to specific threats or campaigns.
- **Why it matters:** Provides structured, context-rich IOCs with associated threat descriptions. Good source of domain and URL IOCs that complement crt.sh.
- **API endpoint:** `https://otx.alienvault.com/api/v1/pulses/subscribed`
- **Requires free API key:** Register at otx.alienvault.com
- **Headers:** `X-OTX-API-KEY: {key}`
- **Fields to extract from each pulse:** `indicators[n].type`, `indicators[n].indicator`, `indicators[n].description`, `created`, `pulse.name`
- **Types to keep:** `domain`, `IPv4`, `URL`, `hostname`

---

## Layer-by-layer implementation guide (Go core + Python LangChain agents)

### Layer 1 — Go collectors (`internal/providers`)

Keep one provider file per source in Go:
- `internal/providers/crtsh.go`
- `internal/providers/shodan.go`
- `internal/providers/urlhaus.go`
- `internal/providers/abuseipdb.go`
- `internal/providers/otx.go`

Each provider returns a common Go model from `pkg/models/threat.go`.

Use a shared interface:

```go
type Provider interface {
    Name() string
    Collect(ctx context.Context) ([]models.Threat, error)
}
```

The collector command (`cmd/collector/main.go`) runs providers concurrently with per-provider rate limiting and timeout guards.

### Layer 2 — Go ingestion + provenance (`internal/ingest`)

Create an ingestion package to normalize provider output and persist provenance.

Core responsibilities:
- Generate stable `event_id` and dedup hash.
- Normalize IOC type (`ip`, `domain`, `url`, `hostname`).
- Attach source metadata: API endpoint, query, collected timestamp.
- Write raw evidence and normalized event to storage.

Recommended Go struct:

```go
type ThreatEvent struct {
    EventID            string
    IOCValue           string
    IOCType            string
    SourceName         string
    SourceURL          string
    SourceQuery        string
    RawEvidenceJSON    string
    CollectedAt        time.Time
    CorroborationCount int
    OpenPorts          []int
    ASN                string
    IsSynthetic        bool
    PoisonAttackType   string
    PoisonDetected     *bool
    DetectionRule      string
    CompositeScore     *float64
    ThreatLevel        string
    DaysToAttack       string
    PipelineStage      string
}
```

### Layer 3 — Go validation, scoring, and API (`internal/validation`, `internal/scoring`, `cmd/api`)

Go owns deterministic pipeline logic:
- Quarantine rules (`SINGLE_SOURCE_FRESH_DOMAIN`, `SUSPICIOUS_TIMESTAMP`, `TTP_BANNER_MISMATCH`).
- Composite scoring and threat level mapping.
- API endpoints for dashboard/reporting.

Suggested API endpoints:
- `GET /health`
- `GET /api/v1/events?stage=scored`
- `GET /api/v1/events/quarantined`
- `GET /api/v1/metrics/pipeline`
- `POST /api/v1/exports/stix`
- `POST /api/v1/exports/report`
- `POST /api/v1/agents/injections/trigger` (manual demo trigger)

### Layer 4 — Python LangChain agents (`agents/`)

Python runs as a separate service and communicates with Go API over HTTP.

Agents to implement:
- `blue_analyst_agent`: summarize highest-risk IOC clusters and create analyst notes.
- `red_injector_agent`: generate synthetic poisoning attempts based on recent real events.
- `triage_agent` (optional): produce action plans for SOC workflows.

LangChain tool wrappers should call Go endpoints instead of direct DB access:
- `get_recent_events`
- `submit_synthetic_event`
- `get_pipeline_metrics`
- `tag_event_notes`

Keep LLM output bounded with strict schemas (Pydantic) before sending back to Go.

### Layer 5 — output generation (`internal/output` + `agents/reporting`)

Primary exports stay Go-native for reliability:
- STIX bundle builder in Go.
- Core PDF/report generator in Go.

Optional Python enhancement:
- LangChain-generated narrative sections inserted into PDF as analyst commentary.

### Layer 6 — SOC-facing surfaces

Use one frontend (Streamlit or web UI) that only calls Go API.
The frontend does not query providers or databases directly.

### Layer 5a — STIX export (`internal/output/stix_exporter.go`)

Generate STIX 2.1 bundles from scored events in Go. Do not overwrite files; always emit timestamped artifacts.

Required output fields per indicator:
- IOC pattern (`ipv4-addr`, `domain-name`, `url`)
- Confidence from composite score
- Source provenance as external references
- Custom properties: days-to-attack, corroboration count, adversarial pass/fail

Output naming convention:
- `artifacts/stix/specter_output_{timestamp}.stix.json`

### Layer 5b — PDF report (`internal/output/report_exporter.go`)

Generate a jury-facing PDF with:
- executive summary
- pipeline integrity table
- top threats
- quarantine log
- full IOC appendix

Optional: call Python blue analyst chain to generate a concise narrative paragraph that is inserted into the summary section.

Output naming convention:
- `artifacts/reports/specter_report_{timestamp}.pdf`

### Layer 5c — dashboard (`dashboards/streamlit_app.py`)

The dashboard only talks to Go API endpoints. It must never read DB files directly.

Minimum panels:
- pipeline metrics (`/api/v1/metrics/pipeline`)
- live scored/quarantined feed (`/api/v1/events`)
- red injection activity (`/api/v1/agents/injections`)
- export actions (`/api/v1/exports/stix`, `/api/v1/exports/report`)

Demo control:
- include a manual button that calls `/api/v1/agents/injections/trigger`.

---

## Build order

Build in this exact sequence. Each step is independently testable.

**Step 1 — Go domain model and config**
Finalize `pkg/models/threat.go` and `internal/config/config.go` for all shared fields and environment variables.

**Step 2 — Go providers and collector command**
Complete all provider collectors and run `cmd/collector/main.go` to verify live ingestion from all sources.

**Step 3 — Go ingestion and storage layer**
Add `internal/ingest` and `internal/storage` packages for normalization, dedup, persistence, and query methods.

**Step 4 — Go validation and scoring engine**
Add `internal/validation` and `internal/scoring` with deterministic rules plus unit tests.

**Step 5 — Go API service**
Create `cmd/api/main.go` and API routes for events, metrics, exports, and manual red injection trigger.

**Step 6 — Python agent service skeleton**
Create `agents/` service with FastAPI, LangChain wiring, and tool adapters to Go endpoints.

**Step 7 — Red and Blue LangChain agents**
Implement red injection generation and blue analyst summarization with schema-validated outputs.

**Step 8 — Cross-service integration tests**
Run end-to-end tests: collector -> ingest -> validate/score -> agent enrichment -> API responses.

**Step 9 — Output generation and demo surfaces**
Finalize STIX/PDF exports and dashboard integration against Go API.

**Step 10 — Demo hardening**
Add observability, retries, deterministic seed mode for red agent, and one-click demo script.

---

## File structure (revised for Go core + Python agents)

```
SPECTER/
├── .env
├── .env.example
├── go.mod
├── go.sum
├── README.md
├── PLAN.md
├── cmd/
│   ├── collector/
│   │   └── main.go                    # Scheduled OSINT collection + ingest trigger
│   ├── api/
│   │   └── main.go                    # REST API server
│   └── worker/
│       └── main.go                    # Validation, scoring, queue consumers
├── internal/
│   ├── config/
│   │   ├── config.go
│   │   └── config_test.go
│   ├── providers/
│   │   ├── crtsh.go
│   │   ├── shodan.go
│   │   ├── urlhaus.go
│   │   ├── abuseipdb.go
│   │   ├── otx.go
│   │   └── *_test.go
│   ├── ingest/
│   │   ├── normalizer.go
│   │   ├── dedupe.go
│   │   └── ingest_test.go
│   ├── storage/
│   │   ├── repository.go
│   │   ├── migrations/
│   │   │   └── 001_init.sql
│   │   └── repository_test.go
│   ├── validation/
│   │   ├── detector.go
│   │   └── detector_test.go
│   ├── scoring/
│   │   ├── scorer.go
│   │   └── scorer_test.go
│   ├── api/
│   │   ├── router.go
│   │   ├── handlers_events.go
│   │   ├── handlers_metrics.go
│   │   └── handlers_exports.go
│   └── output/
│       ├── stix_exporter.go
│       └── report_exporter.go
├── pkg/
│   └── models/
│       └── threat.go
├── agents/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                     # FastAPI service for LangChain agents
│   │   ├── config.py
│   │   ├── schemas.py                  # Pydantic IO contracts
│   │   ├── clients/
│   │   │   └── go_api_client.py
│   │   ├── tools/
│   │   │   ├── event_tools.py
│   │   │   └── injection_tools.py
│   │   ├── chains/
│   │   │   ├── blue_analyst_chain.py
│   │   │   └── red_injector_chain.py
│   │   └── services/
│   │       └── agent_runner.py
│   └── tests/
│       ├── test_blue_agent.py
│       └── test_red_agent.py
├── dashboards/
│   └── streamlit_app.py                # UI against Go API
├── scripts/
│   ├── run_local.sh
│   └── seed_demo_data.sh
└── docs/
    ├── api.md
    └── architecture.md
```

---

## Running the project

**1) Configure environment**
```bash
cp .env.example .env
# edit keys and service URLs
```

**2) Run Go API + worker + collector**
```bash
go run ./cmd/api
go run ./cmd/worker
go run ./cmd/collector
```

**3) Run Python agents service**
```bash
cd agents
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**4) Run dashboard**
```bash
streamlit run dashboards/streamlit_app.py
```

---

## Environment variables

```
# OSINT provider keys
ABUSEIPDB_API_KEY=
OTX_API_KEY=
SHODAN_API_KEY=

# Go services
API_PORT=8080
WORKER_CONCURRENCY=4
COLLECTION_INTERVAL_SECONDS=60
DB_DSN=postgres://specter:specter@localhost:5432/specter?sslmode=disable

# Python agent service
AGENT_SERVICE_PORT=8001
AGENT_MODEL=gpt-4.1-mini
LANGCHAIN_API_KEY=
OPENAI_API_KEY=
GO_API_BASE_URL=http://localhost:8080
RED_AGENT_INTERVAL_SECONDS=30

# Shared
LOG_LEVEL=INFO
DEMO_MODE=true
```

---

## Error handling rules

Apply these everywhere, not just at the edges:

- **Every API call** must be wrapped in try/except. Log the error. Return an empty list. Never crash.
- **Every database write** must be wrapped in try/except. If a write fails, log it and continue.
- **Shodan rate limits:** always `time.sleep(1)` between Shodan API calls. If you get a 429, back off for 60 seconds.
- **crt.sh timeouts:** set `timeout=10` on requests. If it times out, retry once after 5 seconds, then skip.
- **The Red Agent thread:** must be `daemon=True` so it stops when the main process stops. Wrap the injection loop in a broad try/except so a bad injection never kills the thread.
- **The Detector loop:** same — daemon thread, broad try/except in the loop body.

---

## What the demo looks like (build toward this)

The demo takes 10 minutes total. The jury sees:

1. Terminal 1 running with collection logs scrolling — real data coming in from 5 sources.
2. Browser tab open to the Streamlit dashboard — metrics updating, IOC table filling up.
3. You point to a high-scoring IOC. You show the provenance — which API, which query, exact timestamp.
4. You explain the composite score — show each dimension contributing.
5. You say: *"Every pipeline can be poisoned. So we built ours to attack itself."* Red Agent activity panel is already showing injections being caught.
6. You trigger a new injection manually (add a `st.button("Trigger injection now")` to the dashboard for demo purposes). The injection appears. Within seconds — QUARANTINED. Detection rule displayed.
7. You click Export STIX. File downloads. You open it briefly to show it's real JSON.
8. You click Generate PDF. You show the cover page and one threat card.
9. Closing line: *"Other pipelines trust their data. Ours doesn't — and that's why yours should trust ours."*

---

## Limitations to acknowledge in the written report

The hackathon report requires a "limitations" section. Prepare these honestly:

- The Days-to-Attack estimate is a heuristic based on score thresholds, not a trained predictive model. It provides directional guidance, not a precise forecast.
- The Red Injector uses rule-based attack patterns. A real adversarial system would use adaptive techniques. Future work: train the Red Agent using reinforcement learning against the detector.
- Shodan free tier returns limited results and has strict rate limits. A production version would use the paid API or alternative infrastructure scanning sources.
- The pipeline does not currently host a TAXII server. STIX output is file-based. A production version would expose a live TAXII feed endpoint.
- WHOIS data accuracy varies by TLD and registrar. Some registrars obscure registration dates with privacy protection, making domain age unreliable for certain TLDs.
- The pipeline is single-node. A production version would use a message queue (Kafka or RabbitMQ) instead of Python's in-memory queue for horizontal scaling.

---

*This document is the complete specification for SPECTER. Build every layer described here. Do not skip sections. The adversarial mirror in Layer 3 is the project's core innovation — it must work correctly and visibly for the demo to succeed.*
