from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pytest
import requests

BASE_URL = os.getenv("GO_API_BASE_URL")


def _parse_ts(value: Any) -> None:
    if not isinstance(value, str):
        raise AssertionError(f"timestamp must be a string, got {type(value)}")
    datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@pytest.mark.contract
def test_go_health_contract(go_api_base_url: str) -> None:
    resp = requests.get(f"{go_api_base_url}/health", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    assert isinstance(body, dict)
    assert body.get("status") == "ok"


@pytest.mark.contract
def test_go_metrics_contract(go_api_base_url: str) -> None:
    resp = requests.get(f"{go_api_base_url}/api/v1/metrics/pipeline", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    assert isinstance(body, dict)
    for key in ("total_events", "quarantined_count", "scored_count"):
        assert key in body
        assert isinstance(body[key], int)
        assert body[key] >= 0


@pytest.mark.contract
def test_go_events_contract(go_api_base_url: str) -> None:
    resp = requests.get(f"{go_api_base_url}/api/v1/events?limit=1", timeout=10)
    resp.raise_for_status()
    body = resp.json()
    if body is None:
        body = []
    assert isinstance(body, list)
    if len(body) == 0:
        return
    event = body[0]
    assert isinstance(event.get("event_id"), str)
    assert isinstance(event.get("ioc_value"), str)
    assert isinstance(event.get("ioc_type"), str)
    assert isinstance(event.get("source_name"), str)
    _parse_ts(event.get("collected_at"))
    _parse_ts(event.get("created_at"))
    _parse_ts(event.get("updated_at"))


@pytest.mark.contract
def test_go_manual_injection_contract(go_api_base_url: str) -> None:
    payload = {
        "ioc_type": "domain",
        "ioc_value": "jurydemo-contract-9191.example",
        "source_name": "contract_test",
        "raw_evidence": {
            "domain_age_days": 0,
            "cert_metadata": {"issuer": "Let's Encrypt"},
        },
        "is_synthetic": True,
        "poison_attack_type": "GHOST_DOMAIN",
        "corroboration_count": 1,
    }
    resp = requests.post(
        f"{go_api_base_url}/api/v1/agents/injections/trigger",
        json=payload,
        timeout=10,
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body.get("submitted") is True
    assert isinstance(body.get("message"), str)
    assert isinstance(body.get("event_id"), str)
    assert body.get("ioc_value") == payload["ioc_value"]
    assert body.get("ioc_type") == payload["ioc_type"]
    assert isinstance(body.get("stage"), str)
    assert isinstance(body.get("is_synthetic"), bool)
