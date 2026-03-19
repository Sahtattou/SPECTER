# SPECTER API Reference

This document summarizes currently implemented API endpoints.

## Go API

Base URL (default): `http://localhost:8080`

### Health

- `GET /health`
- Response: `{"status":"ok"}`

### Events

- `GET /api/v1/events`
  - Optional query params:
    - `stage` (e.g. `scored`, `quarantined`, `validated`)
    - `limit` (non-negative integer)
- `GET /api/v1/events/quarantined`

### Metrics

- `GET /api/v1/metrics/pipeline`
- Response includes:
  - `total_events`
  - `quarantined_count`
  - `scored_count`

### Exports

- `POST /api/v1/exports/stix`
  - Generates STIX artifact under `artifacts/stix/`
- `POST /api/v1/exports/report`
  - Generates report artifact under `artifacts/reports/`

### Manual injection bridge

- `POST /api/v1/agents/injections/trigger`
- Body fields accepted:
  - `ioc_type`, `ioc_value` (required)
  - `source_name`, `source_url`, `source_query`
  - `raw_evidence`, `collected_at`, `open_ports`, `asn`
  - `corroboration_count`, `is_synthetic`, `poison_attack_type`

## Python Agents API

Base URL (default): `http://localhost:8001`

### Service health

- `GET /health`
- `GET /ready`

### Adversarial mirror endpoints

- `POST /mirror/ingest`
- `POST /mirror/injections/trigger`
- `POST /api/v1/agents/injections/trigger` (alias)
- `GET /mirror/events`
- `GET /mirror/injections`
- `GET /mirror/metrics`

### Agent workflows

- `POST /agents/blue/analyze`
- `POST /agents/red/inject`
- `POST /agents/run`

## Notes

- Go and Python services are intentionally separate surfaces; dashboard primarily consumes agent mirror APIs.
- Current report export is functional but not a fully styled PDF renderer yet.

## Example requests

### List recent events (Go API)

```bash
curl -s "http://localhost:8080/api/v1/events?limit=10"
```

### Get pipeline metrics (Go API)

```bash
curl -s "http://localhost:8080/api/v1/metrics/pipeline"
```

### Trigger manual injection via Go API bridge

```bash
curl -s -X POST "http://localhost:8080/api/v1/agents/injections/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "ioc_type": "domain",
    "ioc_value": "paypal-secure-4821.com",
    "source_name": "manual_injection",
    "is_synthetic": true,
    "poison_attack_type": "GHOST_DOMAIN",
    "corroboration_count": 1,
    "raw_evidence": {"cert_metadata": {"issuer": "Let\'s Encrypt"}}
  }'
```

### Trigger mirror injection directly (Agents API)

```bash
curl -s -X POST "http://localhost:8001/mirror/injections/trigger" \
  -H "Content-Type: application/json" \
  -d '{"attack_type":"TTP_MISMATCH"}'
```

### Read mirror metrics (Agents API)

```bash
curl -s "http://localhost:8001/mirror/metrics"
```
