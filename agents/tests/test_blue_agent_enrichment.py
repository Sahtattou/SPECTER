from __future__ import annotations

from app.adversarial.blue_agent import BlueAgent
from app.adversarial.models import IOCEnvelope


def test_url_normalization_preserves_original_raw_value() -> None:
    agent = BlueAgent(source_clients={})
    envelope = IOCEnvelope(
        raw_value="https://evil-login.example/reset",
        ioc_type="url",
        source_name="otx",
        corroboration_count=0,
    )

    out = agent.enrich(envelope)

    assert out.ioc_type == "domain"
    assert out.raw_value == "evil-login.example"
    assert (
        out.raw_evidence.get("original_raw_value") == "https://evil-login.example/reset"
    )
    assert out.pipeline_stage == "enriched"


def test_domain_whois_age_increments_corroboration() -> None:
    def fake_whois(_: str):
        return {"created_at": "2020-01-01T00:00:00Z"}

    agent = BlueAgent(source_clients={"whois": fake_whois})
    envelope = IOCEnvelope(
        raw_value="long-lived.example",
        ioc_type="domain",
        source_name="otx",
        corroboration_count=0,
    )

    out = agent.enrich(envelope)

    assert isinstance(out.domain_age_days, int)
    assert out.domain_age_days >= 1
    assert out.corroboration_count == 1
    assert "whois" in out.raw_evidence


def test_ip_enrichment_accepts_list_payload_from_client() -> None:
    def fake_abuse(_: str):
        return [{"abuseConfidenceScore": 85}]

    agent = BlueAgent(source_clients={"abuseipdb": fake_abuse})
    envelope = IOCEnvelope(
        raw_value="198.51.100.5",
        ioc_type="ip",
        source_name="otx",
        corroboration_count=0,
    )

    out = agent.enrich(envelope)

    assert out.corroboration_count == 1
    assert isinstance(out.raw_evidence.get("abuseipdb"), list)
