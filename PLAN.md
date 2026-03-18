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

SPECTER has 6 layers. They execute sequentially for each IOC, except Layer 3 which runs concurrently.

```
LAYER 1 — Collection
    Five public APIs queried on a schedule
    Each returns raw signals (IPs, domains, URLs)
         ↓
LAYER 2 — Ingestion & tracing
    Every signal wrapped in a provenance envelope
    Assigned a UUID, stored in SQLite
         ↓
LAYER 3 — Adversarial mirror [TWO AGENTS, ONE QUEUE]
    Blue Agent: enriches real IOCs, builds corroboration count
    Red Agent:  injects synthetic poisoned IOCs (runs in background thread)
    Detector:   applies 3 rules to everything in the queue
    Result: each IOC is either VALIDATED or QUARANTINED
         ↓
LAYER 4 — Scoring
    Each VALIDATED IOC scored 0–100 across 5 weighted dimensions
    Days-to-Attack estimate computed
    Threat level assigned: LOW / MEDIUM / HIGH / CRITICAL
         ↓
LAYER 5 — Output generation
    STIX 2.1 JSON bundle (machine-readable, SOC-importable)
    Threat Narrative PDF (plain English, for analysts and managers)
    Live Streamlit dashboard (demo interface)
         ↓
LAYER 6 — SOC consumption
    Dashboard export buttons
    MISP-compatible STIX file
    PDF download
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

## Layer-by-layer implementation guide

### Layer 1 — collector.py

Write one function per source: `collect_crtsh()`, `collect_shodan()`, `collect_urlhaus()`, `collect_abuseipdb()`, `collect_otx()`. Each function returns a list of dicts with a consistent minimal structure:

```python
{
    "raw_value": str,       # the IP, domain, or URL
    "ioc_type": str,        # 'ip' | 'domain' | 'url'
    "source_name": str,     # 'crtsh' | 'shodan' | 'urlhaus' | 'abuseipdb' | 'otx'
    "source_url": str,      # exact API endpoint called
    "source_query": str,    # query string used
    "raw_response": dict,   # full parsed JSON from API
    "collected_at": str,    # ISO 8601 timestamp
}
```

Write a `collect_all()` function that calls all five, deduplicates by `raw_value`, and returns the combined list.

Handle errors gracefully. If one source is down, log it and continue. Never crash the pipeline because one API is unreachable.

---

### Layer 2 — ingestion.py and db.py

The `IOCEnvelope` is the central data structure of the entire project. Every other layer reads from and writes to it. Define it as a Python dataclass.

```python
@dataclass
class IOCEnvelope:
    # Identity
    ioc_uuid: str              # uuid4, generated at ingestion
    raw_value: str             # the actual IP/domain/URL
    ioc_type: str              # 'ip' | 'domain' | 'url'

    # Provenance (filled at ingestion, never modified)
    source_name: str
    source_url: str
    source_query: str
    raw_evidence: str          # JSON string of full API response
    collected_at: str          # ISO 8601

    # Pipeline state (updated as IOC moves through stages)
    pipeline_stage: str        # 'raw_ingest' → 'enriched' → 'validated' | 'quarantined' → 'scored'

    # Adversarial mirror fields (filled by red_agent.py and detector.py)
    is_synthetic: bool         # True if injected by Red Agent
    poison_attack_type: str | None   # 'REPUTATION_LAUNDERING' | 'GHOST_DOMAIN' | 'TTP_MISMATCH' | 'TIMESTAMP_MANIPULATION'
    poison_detected: bool | None     # True = caught, False = missed, None = not yet checked
    detection_rule: str | None       # which rule triggered

    # Enrichment fields (filled by blue_agent.py)
    corroboration_count: int        # how many sources independently mention this IOC
    domain_age_days: int | None     # for domains only, from WHOIS
    open_ports: list | None         # for IPs only, from Shodan enrichment
    asn: str | None                 # autonomous system number

    # Scoring (filled by scorer.py)
    composite_score: float | None
    score_breakdown: dict | None    # {'corroboration': x, 'infra': x, 'poison_pass': x, 'temporal': x, 'asn': x}
    days_to_attack_estimate: str | None
    threat_level: str | None        # 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

    # Output
    analyst_notes: str | None
```

SQLite stores every envelope. Every field in the dataclass maps to a column. Write `save_ioc(envelope)` and `update_ioc(envelope)` functions. Write `get_all_iocs()`, `get_clean_iocs()`, `get_quarantined_iocs()`, and `get_recent_iocs(limit=50)` for the dashboard.

---

### Layer 3 — The adversarial mirror

This is the most important layer technically. Read this section carefully.

**The shared queue** is a `queue.Queue()` instance in `queue_manager.py`. Both the Blue Agent and the Red Agent call `enqueue(envelope)` to add IOCs. The Detector calls `dequeue()` to process them. Neither agent knows which IOCs in the queue came from the other.

**blue_agent.py** takes the raw `IOCEnvelope` from the collector output and enriches it before enqueueing:
- For domains: look up WHOIS age using `python-whois`. Store `domain_age_days`.
- For IPs: check if this IP appears in AbuseIPDB (if the source wasn't already AbuseIPDB). Store in `corroboration_count`.
- For any IOC: check if the same `raw_value` exists in another source already in the SQLite database. If yes, increment `corroboration_count`.
- Update `pipeline_stage` to `'enriched'`.
- Call `enqueue(envelope)`.

**red_agent.py** runs in a `daemon=True` background thread. Every `RED_AGENT_INTERVAL` seconds (default 30), it generates one poisoned envelope and calls `enqueue()` on it. It also writes the injection to a separate `injections` log table in SQLite for the dashboard to display.

The four attack types in detail:

**REPUTATION_LAUNDERING:** Pull a real IP from the AbuseIPDB data already collected in the last cycle (stored in SQLite). Create a new envelope for that IP. Set `source_name='otx'` (forging a more trusted source), set `corroboration_count=0` (no cross-source confirmation), and set `abuseConfidenceScore` to a low value in the raw_evidence dict. The attack pretends this known-bad IP is a fresh, unverified OTX report rather than an AbuseIPDB confirmed-bad IP. The goal is to make the pipeline score it low and not flag it.

**GHOST_DOMAIN:** Generate a plausible lookalike domain. Pattern: `{brand}-{action}-{random}.{tld}` where brand is one of `['paypal', 'microsoft', 'google', 'amazon']`, action is one of `['secure', 'verify', 'login', 'account', 'update']`, random is a 4-digit number, and tld is `.com` or `.net`. Set `domain_age_days=0` (just registered), `corroboration_count=1`, and forge a clean cert in the raw_evidence. The attack tries to insert a brand-new phishing domain that looks plausible but has zero corroboration.

**TTP_MISMATCH:** Pull a real IP from the Shodan data that has port 50050 open. Create a synthetic envelope for it. In the `raw_evidence`, forge the banner to say `"product": "Cloudflare CDN"` and `"org": "Cloudflare Inc."`. Set `corroboration_count=3` to make it look well-trusted. The attack claims a known C2 server is actually a legitimate CDN node.

**TIMESTAMP_MANIPULATION:** Pull any real IOC already in the SQLite database that has a `composite_score` above 60. Clone it with a new UUID. Set `collected_at` to 30 days ago. The attack attempts to make a fresh threat indicator appear aged and therefore more trustworthy to any time-based confidence boost.

**detector.py** applies exactly three rules to every IOC dequeued. Rules are applied in order. If any rule triggers, the IOC is quarantined and no further rules are checked.

Rule 1 — **SINGLE_SOURCE_HIGH_SCORE:**
```
Condition: corroboration_count == 1 AND domain_age_days is not None AND domain_age_days < 7
Action: QUARANTINE
Rationale: A domain less than 7 days old with only one source reporting it cannot have
earned legitimacy. Fresh domains appearing in only one feed = very likely synthetic injection
or extremely early-stage threat (both should be quarantined pending further verification).
```

Rule 2 — **SUSPICIOUS_TIMESTAMP:**
```
Condition: The collected_at timestamp is more than 20 days ago AND the ioc_uuid does not
exist in the historical pipeline runs table (i.e., it wasn't actually collected 20 days ago —
it appeared fresh in the queue with a backdated timestamp)
Action: QUARANTINE
Rationale: Catches TIMESTAMP_MANIPULATION. Real old IOCs appear continuously in historical
runs. An "old" IOC with no prior run history is a forged timestamp.
```

Rule 3 — **TTP_BANNER_MISMATCH:**
```
Condition: ioc_type == 'ip' AND 50050 in open_ports AND 'cloudflare' in raw_evidence.lower()
Action: QUARANTINE
Rationale: Cloudflare does not run Cobalt Strike listeners. Port 50050 + Cloudflare branding
= internal contradiction = injected IOC. Extend this logic: any CDN org name combined with
offensive framework ports is a mismatch.
```

For every IOC that passes all 3 rules: set `poison_detected=False`, `pipeline_stage='validated'`.
For every IOC caught by a rule: set `poison_detected=True`, `detection_rule=<rule name>`, `pipeline_stage='quarantined'`.

Save to SQLite after every detection decision.

---

### Layer 4 — scorer.py

Only call this on IOCs with `pipeline_stage='validated'`. Never score quarantined IOCs.

Five dimensions, each produces a 0–100 sub-score. Weights are hardcoded constants at the top of the file so they can be adjusted easily.

```python
WEIGHTS = {
    'corroboration': 0.25,
    'infra_fingerprint': 0.25,
    'poison_pass': 0.20,
    'temporal': 0.15,
    'asn_reputation': 0.15,
}
```

**Corroboration score:** `min(corroboration_count / 3.0, 1.0) * 100`
Three or more independent sources = max score. One source = 33. Zero = 0.

**Infrastructure fingerprint score:**
- 100 if any of these ports are in `open_ports`: 50050 (Cobalt Strike), 40056 (Havoc), 8888 (Sliver), 4444 (Metasploit default)
- 70 if ports include 3389 (RDP) or 22 (SSH) on a non-cloud ASN
- 40 if domain has SAN count > 10 in cert data (bulletproof hosting indicator)
- 20 if nothing suspicious found

**Poison pass score:**
- 100 if `poison_detected == False` (passed all detection rules)
- 0 if `poison_detected == True` (never reaches this function in practice, but handle it)

**Temporal recency score:** `max(0, 100 - (hours_since_collected * 2))`
An IOC collected less than 1 hour ago scores close to 100. One collected 48 hours ago scores ~4. Encourages SOC analysts to act on fresh intelligence.

**ASN reputation score:**
Maintain a hardcoded list of ASNs known for bulletproof hosting. Use the list from public threat intel reports (freely available). If the IOC's ASN is in the list: 100. If ASN is unknown or residential: 50. If ASN belongs to a major cloud provider (AWS, GCP, Azure, Cloudflare): 20 (cloud providers are commonly abused but also legitimately used — medium score, not high).

**Composite score formula:**
```python
composite = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
# Hard cap: if the IOC's poison_pass score is 0, cap composite at 50
if scores['poison_pass'] == 0:
    composite = min(composite, 50.0)
composite = round(composite, 1)
```

**Days-to-Attack estimate (heuristic):**
```python
if composite >= 85:   return '24–48 hours'
elif composite >= 70: return '3–5 days'
elif composite >= 55: return '5–10 days'
elif composite >= 40: return '10–20 days'
else:                 return 'unlikely / insufficient data'
```

**Threat level:**
```python
if composite >= 80:   return 'CRITICAL'
elif composite >= 60: return 'HIGH'
elif composite >= 40: return 'MEDIUM'
else:                 return 'LOW'
```

After scoring, set `pipeline_stage='scored'` and save to SQLite.

---

### Layer 5a — stix_exporter.py

Use the `stix2` Python library. This is not optional — hand-crafting STIX JSON is error-prone and won't import cleanly into MISP.

For each scored IOC, create a `stix2.Indicator` object:

```python
stix2.Indicator(
    name=f"SPECTER: {envelope.ioc_type.upper()} — {envelope.raw_value}",
    description=envelope.analyst_notes,
    pattern=build_pattern(envelope),          # see below
    pattern_type="stix",
    confidence=int(envelope.composite_score),
    labels=["malicious-activity"],
    kill_chain_phases=[build_kill_chain(envelope)],
    external_references=[{
        "source_name": envelope.source_name,
        "url": envelope.source_url,
        "description": f"Original evidence collected at {envelope.collected_at}"
    }],
    custom_properties={
        "x_specter_days_to_attack": envelope.days_to_attack_estimate,
        "x_specter_corroboration_count": envelope.corroboration_count,
        "x_specter_passed_adversarial_test": not envelope.poison_detected,
    }
)
```

Pattern builder:
```python
def build_pattern(envelope: IOCEnvelope) -> str:
    if envelope.ioc_type == 'ip':
        return f"[ipv4-addr:value = '{envelope.raw_value}']"
    elif envelope.ioc_type == 'domain':
        return f"[domain-name:value = '{envelope.raw_value}']"
    elif envelope.ioc_type == 'url':
        return f"[url:value = '{envelope.raw_value}']"
```

Kill chain phase builder:
```python
def build_kill_chain(envelope: IOCEnvelope) -> stix2.KillChainPhase:
    if envelope.threat_level == 'CRITICAL':
        return stix2.KillChainPhase(kill_chain_name="mitre-attack", phase_name="command-and-control")
    elif envelope.threat_level == 'HIGH':
        return stix2.KillChainPhase(kill_chain_name="mitre-attack", phase_name="resource-development")
    else:
        return stix2.KillChainPhase(kill_chain_name="mitre-attack", phase_name="reconnaissance")
```

Wrap all indicators in a `stix2.Bundle` and write to `specter_output_{timestamp}.stix.json`. The timestamp must be in the filename — never overwrite previous runs.

---

### Layer 5b — pdf_reporter.py

Use `reportlab`. The PDF has 6 sections. Keep the design clean and professional — this goes in front of a jury.

**Section 1 — Cover page**
- "SPECTER" large, centered
- "Threat Intelligence Briefing" subtitle
- Run date and time
- "Confidential — For SOC Use Only" footer
- Pipeline health score as a large number (e.g. "94% pipeline integrity")

**Section 2 — Executive summary**
Two short paragraphs. Auto-generate from run statistics:
- Para 1: "During this pipeline run, SPECTER collected X IOCs from 5 public OSINT sources. After adversarial validation and scoring, Y IOCs were confirmed as credible threat signals."
- Para 2: "The Red Injector attempted Z poisoning attacks. The detector caught W of them (X%). The pipeline integrity score for this run is Y%."

**Section 3 — Pipeline health table**
4-column table: Injections attempted | Caught | Missed | Integrity score

**Section 4 — Top 5 threats**
For the 5 highest-scoring clean IOCs. Each gets a "card" layout:
- IOC value (large, monospaced font)
- Type badge, Threat level badge (color-coded), Days-to-Attack estimate
- Composite score as a horizontal bar
- Source chain: "Collected from {source_name} at {collected_at}"
- Why it's suspicious: auto-generated rationale (see rationale generator below)

**Rationale generator:**
```python
def generate_rationale(envelope: IOCEnvelope) -> str:
    reasons = []
    if envelope.corroboration_count >= 3:
        reasons.append(f"independently confirmed by {envelope.corroboration_count} sources")
    if envelope.score_breakdown.get('infra_fingerprint', 0) >= 80:
        reasons.append("infrastructure fingerprint matches known offensive framework")
    if envelope.domain_age_days is not None and envelope.domain_age_days < 7:
        reasons.append(f"domain registered only {envelope.domain_age_days} days ago")
    if envelope.score_breakdown.get('asn_reputation', 0) >= 80:
        reasons.append("hosted on ASN with bulletproof hosting history")
    if not reasons:
        reasons.append("elevated composite score across multiple dimensions")
    return "Flagged because it was " + "; ".join(reasons) + "."
```

**Section 5 — Quarantine log**
Table of all quarantined IOCs: IOC value | Attack type | Detection rule | Would-be score (what it would have scored if not caught)

**Section 6 — Full IOC appendix**
Complete sorted list of all scored clean IOCs with scores.

Output: `specter_report_{timestamp}.pdf`

---

### Layer 5c — dashboard.py

The dashboard is what the jury sees projected on screen during the demo. It must look impressive, update live, and tell a clear story.

Use Streamlit. Structure:

```python
import streamlit as st
import time

st.set_page_config(page_title="SPECTER", layout="wide", page_icon="🔍")

# Auto-refresh every 5 seconds
while True:
    iocs = db.get_recent_iocs(limit=100)
    injections = db.get_recent_injections(limit=20)
    
    # Header row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pipeline integrity", f"{pipeline_health_score}%")
    col2.metric("IOCs collected", total_iocs)
    col3.metric("Threats confirmed", clean_high_score_count)
    col4.metric("Injections caught", f"{caught}/{attempted}")
    
    # Two-panel layout
    left, right = st.columns([2, 1])
    
    with left:
        st.subheader("Live IOC feed")
        # Dataframe with color-coded rows
        # CRITICAL = red, HIGH = orange, MEDIUM = yellow, QUARANTINED = dark red
    
    with right:
        st.subheader("Red agent activity")
        # Table of recent injection attempts
        # Each row: timestamp, attack type, CAUGHT/MISSED badge
    
    # Histogram of composite scores
    st.plotly_chart(score_distribution_chart(iocs))
    
    # Export buttons
    col_a, col_b = st.columns(2)
    if col_a.button("Export STIX bundle"):
        stix_exporter.export_stix_bundle(...)
        st.success("STIX bundle exported")
    if col_b.button("Generate PDF report"):
        pdf_reporter.generate_pdf(...)
        st.success("PDF report generated")
    
    time.sleep(5)
    st.rerun()
```

Color-code the IOC table rows: `threat_level == 'CRITICAL'` → red background, `'HIGH'` → orange, `pipeline_stage == 'quarantined'` → dark red with strikethrough on the value.

---

## Build order

Build in this exact sequence. Each step produces something testable before moving to the next.

**Step 1 — Database foundation**
Create `storage/schema.sql`, `storage/db.py`. Write `init_db()`, `save_ioc()`, `update_ioc()`, and all query functions. Test: initialize DB, insert a dummy envelope, query it back.

**Step 2 — Data model**
Create `pipeline/ingestion.py` with the `IOCEnvelope` dataclass and `ingest(raw_signal) -> IOCEnvelope` function. Test: pass a manually constructed raw signal dict, get back a valid envelope with a UUID.

**Step 3 — Collection**
Create `pipeline/collector.py`. Implement all 5 sources. Test each individually with live API calls. Confirm you're getting data. Add error handling.

**Step 4 — Blue agent and queue**
Create `pipeline/queue_manager.py` and `pipeline/blue_agent.py`. Test the full collection → ingest → enrich → enqueue flow. Check SQLite after a run.

**Step 5 — Red agent**
Create `pipeline/red_agent.py`. Test each of the 4 attack types independently. Confirm injected IOCs appear in the queue alongside real ones.

**Step 6 — Detector**
Create `pipeline/detector.py`. Run the detector loop against a queue containing both real and synthetic IOCs. Confirm: synthetic IOCs get quarantined, real ones get validated. Unit test all 3 rules in `tests/test_detector.py`.

**Step 7 — Scorer**
Create `pipeline/scorer.py`. Run against validated IOCs. Check that scores look reasonable, Days-to-Attack estimates make sense, threat levels are correct.

**Step 8 — STIX exporter**
Create `output/stix_exporter.py`. Generate a test bundle. Validate it validates with `stix2` library's built-in validation. Open the JSON and confirm it's well-formed.

**Step 9 — Dashboard**
Create `output/dashboard.py`. Run it with data already in SQLite from previous steps. Confirm metrics display, table updates, export buttons work.

**Step 10 — PDF reporter**
Create `output/pdf_reporter.py`. Generate a test PDF. Open it. Confirm all sections render correctly.

**Step 11 — main.py and integration**
Wire everything together. Run the full pipeline end-to-end with all threads. Confirm the Red Agent is firing, the Detector is catching, the dashboard is updating.

---

## File structure

```
specter/
├── .env                       # API keys — never commit this
├── .env.example               # Template with key names, no values
├── main.py                    # Entry point
├── config.py                  # Loads .env, defines constants
├── requirements.txt
├── pipeline/
│   ├── __init__.py
│   ├── collector.py           # Layer 1
│   ├── ingestion.py           # Layer 2 — IOCEnvelope dataclass lives here
│   ├── queue_manager.py       # Shared queue
│   ├── blue_agent.py          # Layer 3a
│   ├── red_agent.py           # Layer 3b
│   ├── detector.py            # Layer 3c
│   └── scorer.py              # Layer 4
├── output/
│   ├── __init__.py
│   ├── stix_exporter.py       # Layer 5a
│   ├── pdf_reporter.py        # Layer 5b
│   └── dashboard.py           # Layer 5c — run with: streamlit run output/dashboard.py
├── storage/
│   ├── __init__.py
│   ├── db.py
│   └── schema.sql
├── tests/
│   └── test_detector.py
└── data/
    └── specter.db             # Created automatically on first run
```

---

## Running the project

**Install dependencies:**
```bash
pip install requests schedule python-dotenv stix2 reportlab streamlit plotly python-whois
```

**Configure:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Initialize database:**
```bash
python -c "from storage.db import init_db; init_db()"
```

**Run pipeline (terminal 1):**
```bash
python main.py
```

**Run dashboard (terminal 2):**
```bash
streamlit run output/dashboard.py
```

---

## Environment variables

```
ABUSEIPDB_API_KEY=          # from abuseipdb.com (free)
OTX_API_KEY=                # from otx.alienvault.com (free)
SHODAN_API_KEY=             # from shodan.io (free)
RED_AGENT_INTERVAL=30       # seconds between injections (use 30 for demo)
COLLECTION_INTERVAL=60      # seconds between collection cycles
LOG_LEVEL=INFO
DB_PATH=data/specter.db
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
