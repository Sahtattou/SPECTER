#!/usr/bin/env bash
set -euo pipefail

GO_API_BASE_URL="${GO_API_BASE_URL:-http://localhost:8080}"

post_injection() {
  local payload="$1"
  curl -sS -X POST "${GO_API_BASE_URL}/api/v1/agents/injections/trigger" \
    -H "Content-Type: application/json" \
    -d "$payload"
}

echo "[seed] injecting realistic demo dataset into ${GO_API_BASE_URL}"

post_injection '{"ioc_type":"domain","ioc_value":"paypal-secure-4821.com","source_name":"otx","raw_evidence":{"domain_age_days":0,"cert_metadata":{"issuer":"Let\"s Encrypt"}},"is_synthetic":true,"poison_attack_type":"GHOST_DOMAIN","corroboration_count":1}' >/dev/null
post_injection '{"ioc_type":"ip","ioc_value":"198.51.100.42","source_name":"shodan","open_ports":[50050,80],"raw_evidence":{"banner":"Cloudflare edge node"},"is_synthetic":true,"poison_attack_type":"TTP_MISMATCH","corroboration_count":3}' >/dev/null
post_injection '{"ioc_type":"ip","ioc_value":"203.0.113.77","source_name":"otx","raw_evidence":{"abuseConfidenceScore":5},"is_synthetic":true,"poison_attack_type":"REPUTATION_LAUNDERING","corroboration_count":0}' >/dev/null
post_injection '{"ioc_type":"domain","ioc_value":"microsoft-login-9912.net","source_name":"urlhaus","raw_evidence":{"domain_age_days":12},"is_synthetic":false,"corroboration_count":3}' >/dev/null
post_injection '{"ioc_type":"ip","ioc_value":"45.9.148.114","source_name":"abuseipdb","open_ports":[22,3389],"raw_evidence":{"abuseConfidenceScore":85},"is_synthetic":false,"corroboration_count":4}' >/dev/null

echo "[seed] done. quick checks:"
curl -sS "${GO_API_BASE_URL}/api/v1/metrics/pipeline"
echo
