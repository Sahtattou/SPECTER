from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Protocol

from app.schemas import RedInjectionResponse


class RedChainClient(Protocol):
    def get_recent_events(
        self, limit: int = 100, stage: str | None = None
    ) -> List[Dict[str, Any]]: ...

    def submit_synthetic_event(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...


ATTACK_TYPES = [
    "REPUTATION_LAUNDERING",
    "GHOST_DOMAIN",
    "TTP_MISMATCH",
    "TIMESTAMP_MANIPULATION",
]

BRANDS = ["paypal", "microsoft", "google", "amazon"]
ACTIONS = ["secure", "verify", "login", "account", "update"]
TLDS = ["com", "net"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_payload(
    attack_type: str, seed_events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    seed = seed_events[0] if seed_events else {}
    payload: Dict[str, Any] = {
        "is_synthetic": True,
        "poison_attack_type": attack_type,
        "collected_at": _now_iso(),
        "source_name": "red_injector",
        "raw_evidence": {"generated_by": "red_injector_chain"},
    }

    if attack_type == "GHOST_DOMAIN":
        random_suffix = random.randint(1000, 9999)
        domain = f"{random.choice(BRANDS)}-{random.choice(ACTIONS)}-{random_suffix}.{random.choice(TLDS)}"
        payload.update(
            {
                "ioc_type": "domain",
                "ioc_value": domain,
                "corroboration_count": 1,
                "domain_age_days": 0,
            }
        )
        return payload

    if attack_type == "TTP_MISMATCH":
        ip_value = str(seed.get("ioc_value") or "198.51.100.42")
        payload.update(
            {
                "ioc_type": "ip",
                "ioc_value": ip_value,
                "open_ports": [50050],
                "corroboration_count": 3,
                "raw_evidence": {
                    "generated_by": "red_injector_chain",
                    "banner": "Cloudflare CDN",
                    "org": "Cloudflare Inc.",
                },
            }
        )
        return payload

    if attack_type == "TIMESTAMP_MANIPULATION":
        cloned_value = str(seed.get("ioc_value") or "example-phish-login.net")
        payload.update(
            {
                "ioc_type": str(seed.get("ioc_type") or "domain"),
                "ioc_value": cloned_value,
                "collected_at": "2025-02-01T00:00:00Z",
                "corroboration_count": int(seed.get("corroboration_count") or 2),
            }
        )
        return payload

    ip_value = str(seed.get("ioc_value") or "203.0.113.77")
    payload.update(
        {
            "ioc_type": "ip",
            "ioc_value": ip_value,
            "source_name": "otx",
            "corroboration_count": 0,
            "raw_evidence": {
                "generated_by": "red_injector_chain",
                "abuseConfidenceScore": 10,
                "note": "synthetic reputation laundering attempt",
            },
        }
    )
    return payload


def run_red_injector_chain(
    client: RedChainClient,
    attack_type: str | None = None,
    dry_run: bool = True,
) -> RedInjectionResponse:
    selected_attack = attack_type or random.choice(ATTACK_TYPES)
    seed_events = client.get_recent_events(limit=10)
    payload = _build_payload(selected_attack, seed_events)

    if dry_run:
        return RedInjectionResponse(
            attack_type=selected_attack,
            payload=payload,
            submitted=False,
            target_endpoint="/api/v1/agents/injections/trigger",
            notes="Dry run enabled; payload not submitted.",
        )

    result = client.submit_synthetic_event(payload)
    submitted = bool(result.get("submitted", True))
    return RedInjectionResponse(
        attack_type=selected_attack,
        payload=payload,
        submitted=submitted,
        target_endpoint="/api/v1/agents/injections/trigger",
        notes="Payload submitted to Go API."
        if submitted
        else "Go API call returned not submitted.",
    )
