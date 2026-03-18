from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.adversarial.models import IOCEnvelope, utc_now_iso
from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.storage import AdversarialStorage

logger = logging.getLogger(__name__)

ATTACK_TYPES = [
    "REPUTATION_LAUNDERING",
    "GHOST_DOMAIN",
    "TTP_MISMATCH",
    "TIMESTAMP_MANIPULATION",
]

BRANDS = ["paypal", "microsoft", "google", "amazon", "apple"]
ACTIONS = ["secure", "verify", "login", "account", "update"]
TLDS = ["com", "net"]


class RedAgent:
    def __init__(
        self,
        queue_manager: SharedQueueManager,
        storage: AdversarialStorage,
        *,
        interval_seconds: int = 30,
    ) -> None:
        self.queue_manager = queue_manager
        self.storage = storage
        self.interval_seconds = max(1, int(interval_seconds))
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="specter-red-agent", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def inject_now(self, attack_type: Optional[str] = None) -> IOCEnvelope:
        selected_attack = attack_type or random.choice(ATTACK_TYPES)
        envelope = self._generate_attack(selected_attack)
        self.storage.log_injection(
            attack_type=envelope.poison_attack_type or selected_attack,
            raw_value=envelope.raw_value,
            ioc_uuid=envelope.ioc_uuid,
        )
        self.queue_manager.enqueue(envelope)
        return envelope

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.inject_now()
            except Exception as exc:
                logger.exception(
                    "red_agent_injection_cycle_failed", extra={"error": str(exc)}
                )

            if self._stop_event.wait(self.interval_seconds):
                return

    def _generate_attack(self, attack_type: str) -> IOCEnvelope:
        if attack_type == "REPUTATION_LAUNDERING":
            return self._reputation_laundering()
        if attack_type == "GHOST_DOMAIN":
            return self._ghost_domain()
        if attack_type == "TTP_MISMATCH":
            return self._ttp_mismatch()
        return self._timestamp_manipulation()

    def _recent_events(self) -> List[Dict[str, Any]]:
        return self.storage.get_recent_events(limit=500)

    def _reputation_laundering(self) -> IOCEnvelope:
        candidates = [
            event
            for event in self._recent_events()
            if event.get("ioc_type") == "ip"
            and str(event.get("source_name", "")).lower() == "abuseipdb"
            and self._abuse_score(event) >= 70
        ]
        seed = random.choice(candidates) if candidates else None
        ip_value = str(seed.get("raw_value") if seed else "203.0.113.77")

        return IOCEnvelope(
            ioc_uuid=str(uuid4()),
            raw_value=ip_value,
            ioc_type="ip",
            source_name="otx",
            source_query=ip_value,
            raw_evidence={
                "abuseConfidenceScore": 5,
                "note": "synthetic reputation laundering",
                "origin": "red_agent",
            },
            collected_at=utc_now_iso(),
            pipeline_stage="enriched",
            is_synthetic=True,
            poison_attack_type="REPUTATION_LAUNDERING",
            corroboration_count=0,
        )

    def _ghost_domain(self) -> IOCEnvelope:
        suffix = random.randint(1000, 9999)
        domain = f"{random.choice(BRANDS)}-{random.choice(ACTIONS)}-{suffix}.{random.choice(TLDS)}"

        return IOCEnvelope(
            ioc_uuid=str(uuid4()),
            raw_value=domain,
            ioc_type="domain",
            source_name="otx",
            source_query=domain,
            raw_evidence={
                "cert_metadata": {
                    "issuer": "Let's Encrypt",
                    "issued_at": datetime.now(timezone.utc).date().isoformat(),
                },
                "origin": "red_agent",
            },
            collected_at=utc_now_iso(),
            pipeline_stage="enriched",
            is_synthetic=True,
            poison_attack_type="GHOST_DOMAIN",
            corroboration_count=1,
            domain_age_days=0,
        )

    def _ttp_mismatch(self) -> IOCEnvelope:
        candidates = [
            event
            for event in self._recent_events()
            if event.get("ioc_type") == "ip"
            and str(event.get("source_name", "")).lower() == "shodan"
            and 50050
            in [
                int(port)
                for port in (event.get("open_ports") or [])
                if str(port).isdigit()
            ]
        ]
        seed = random.choice(candidates) if candidates else None
        ip_value = str(seed.get("raw_value") if seed else "198.51.100.42")

        return IOCEnvelope(
            ioc_uuid=str(uuid4()),
            raw_value=ip_value,
            ioc_type="ip",
            source_name="shodan",
            source_query=ip_value,
            raw_evidence={
                "banner": "Cloudflare CDN edge node",
                "org": "Cloudflare Inc.",
                "origin": "red_agent",
            },
            collected_at=utc_now_iso(),
            pipeline_stage="enriched",
            is_synthetic=True,
            poison_attack_type="TTP_MISMATCH",
            corroboration_count=3,
            open_ports=[50050],
        )

    def _timestamp_manipulation(self) -> IOCEnvelope:
        candidates = [
            event
            for event in self._recent_events()
            if float(event.get("composite_score") or 0.0) > 60.0
        ]
        seed = random.choice(candidates) if candidates else None
        value = str(seed.get("raw_value") if seed else "paypal-login-alert-3133.com")
        ioc_type = str(seed.get("ioc_type") if seed else "domain")
        historical_timestamp = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat()
        seed_corroboration = (
            seed.get("corroboration_count") if isinstance(seed, dict) else None
        )
        corroboration_count = self._safe_int(seed_corroboration, default=2)

        seed_composite = seed.get("composite_score") if isinstance(seed, dict) else None
        composite_score = self._safe_float(seed_composite, default=61.0)

        seed_ports = seed.get("open_ports") if isinstance(seed, dict) else []
        open_ports: List[int] = []
        if isinstance(seed_ports, list):
            for port in seed_ports:
                try:
                    open_ports.append(self._safe_int(port, default=-1))
                except (TypeError, ValueError):
                    continue
        open_ports = [port for port in open_ports if port >= 0]

        return IOCEnvelope(
            ioc_uuid=str(uuid4()),
            raw_value=value,
            ioc_type=ioc_type,
            source_name=str(seed.get("source_name") if seed else "otx"),
            source_query=value,
            raw_evidence=(seed.get("raw_evidence") if isinstance(seed, dict) else {})
            or {"origin": "red_agent"},
            collected_at=historical_timestamp,
            pipeline_stage="enriched",
            is_synthetic=True,
            poison_attack_type="TIMESTAMP_MANIPULATION",
            corroboration_count=corroboration_count,
            domain_age_days=seed.get("domain_age_days")
            if isinstance(seed, dict)
            else None,
            open_ports=open_ports,
            asn=seed.get("asn") if isinstance(seed, dict) else None,
            composite_score=composite_score,
        )

    @staticmethod
    def _abuse_score(event: dict) -> int:
        evidence = event.get("raw_evidence") or {}
        if isinstance(evidence, dict):
            abuse = evidence.get("abuseipdb") or evidence
            try:
                return RedAgent._safe_int(
                    abuse.get("abuseConfidenceScore")
                    or abuse.get("abuse_confidence_score")
                    or 0,
                    default=0,
                )
            except (TypeError, ValueError):
                return 0
        return 0

    @staticmethod
    def _safe_int(value: object, *, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    @staticmethod
    def _safe_float(value: object, *, default: float) -> float:
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default
