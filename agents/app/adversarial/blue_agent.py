from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.adversarial.models import IOCEnvelope

logger = logging.getLogger(__name__)


class BlueAgent:
    def __init__(self, source_clients: Dict[str, Any]) -> None:
        self.source_clients = source_clients

    def enrich(self, envelope: IOCEnvelope) -> IOCEnvelope:
        corroboration = max(0, int(envelope.corroboration_count or 0))

        if envelope.ioc_type == "url":
            host = self._extract_host(envelope.raw_value)
            if host:
                evidence = (
                    envelope.raw_evidence
                    if isinstance(envelope.raw_evidence, dict)
                    else {}
                )
                evidence.setdefault("original_raw_value", envelope.raw_value)
                envelope.raw_evidence = evidence
                envelope.ioc_type = "domain"
                envelope.raw_value = host

        if envelope.ioc_type == "ip":
            evidence = (
                envelope.raw_evidence if isinstance(envelope.raw_evidence, dict) else {}
            )

            if self._should_query(envelope.source_name, "abuseipdb"):
                abuse = self._safe_call("abuseipdb", envelope.raw_value)
                if abuse:
                    evidence["abuseipdb"] = abuse
                    corroboration += 1

            if self._should_query(envelope.source_name, "shodan"):
                shodan = self._safe_call("shodan", envelope.raw_value, sleep_after=1.0)
                if shodan:
                    evidence["shodan"] = shodan
                    ports = self._extract_open_ports(shodan)
                    if ports:
                        envelope.open_ports = ports
                    asn = self._extract_asn(shodan)
                    if asn:
                        envelope.asn = asn
                    corroboration += 1

            envelope.raw_evidence = evidence

        elif envelope.ioc_type == "domain":
            evidence = (
                envelope.raw_evidence if isinstance(envelope.raw_evidence, dict) else {}
            )

            whois_data = self._safe_call("whois", envelope.raw_value)
            if whois_data:
                age_days = self._extract_domain_age_days(whois_data)
                if age_days is not None:
                    envelope.domain_age_days = age_days
                    corroboration += 1
                evidence["whois"] = whois_data

            if self._should_query(envelope.source_name, "urlhaus"):
                urlhaus = self._safe_call("urlhaus", envelope.raw_value)
                if self._is_confirmation(urlhaus):
                    corroboration += 1
                if urlhaus:
                    evidence["urlhaus"] = urlhaus

            if self._should_query(envelope.source_name, "otx"):
                otx = self._safe_call("otx", envelope.raw_value)
                if self._is_confirmation(otx):
                    corroboration += 1
                if otx:
                    evidence["otx"] = otx

            envelope.raw_evidence = evidence

        envelope.corroboration_count = corroboration
        envelope.pipeline_stage = "enriched"
        return envelope

    @staticmethod
    def _extract_host(url_value: str) -> Optional[str]:
        try:
            parsed = urlparse(url_value)
            return parsed.hostname
        except Exception:
            return None

    @staticmethod
    def _extract_open_ports(payload: Dict[str, Any]) -> List[int]:
        ports = payload.get("open_ports") or payload.get("ports") or []
        result: List[int] = []
        for port in ports:
            try:
                result.append(int(port))
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _extract_asn(payload: Dict[str, Any]) -> Optional[str]:
        asn = payload.get("asn") or payload.get("ASN")
        return str(asn) if asn else None

    @staticmethod
    def _extract_domain_age_days(payload: Dict[str, Any]) -> Optional[int]:
        created_at = (
            payload.get("created_at")
            or payload.get("creation_date")
            or payload.get("registered_at")
        )
        if not created_at:
            return None

        if isinstance(created_at, datetime):
            created_dt = created_at.astimezone(timezone.utc)
        else:
            try:
                created_dt = datetime.fromisoformat(
                    str(created_at).replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except ValueError:
                return None

        now = datetime.now(timezone.utc)
        delta = now - created_dt
        return max(0, int(delta.days))

    @staticmethod
    def _is_confirmation(payload: Optional[Dict[str, Any]]) -> bool:
        if not payload:
            return False
        if isinstance(payload.get("confirmed"), bool):
            return payload["confirmed"]
        if isinstance(payload.get("count"), int):
            return payload["count"] > 0
        if isinstance(payload.get("matches"), list):
            return len(payload["matches"]) > 0
        if isinstance(payload.get("pulse_count"), int):
            return payload["pulse_count"] > 0
        if isinstance(payload.get("query_status"), str):
            return payload["query_status"].lower() == "ok"
        return False

    @staticmethod
    def _normalized_source(source_name: str) -> str:
        normalized = (source_name or "").strip().lower()
        mapping = {
            "abuseipdb": "abuseipdb",
            "shodan": "shodan",
            "urlhaus": "urlhaus",
            "otx": "otx",
            "alienvault otx": "otx",
            "crt.sh": "crt.sh",
            "whois": "whois",
        }
        return mapping.get(normalized, normalized)

    def _should_query(self, original_source: str, target_source: str) -> bool:
        return self._normalized_source(original_source) != self._normalized_source(
            target_source
        )

    def _safe_call(
        self, source_name: str, value: str, *, sleep_after: float = 0.0
    ) -> Optional[Any]:
        client = self.source_clients.get(source_name)
        if client is None:
            return None

        try:
            result = client(value)
            if sleep_after > 0:
                time.sleep(sleep_after)
            if isinstance(result, (dict, list)):
                return result
            return {"raw": str(result)}
        except Exception as exc:
            logger.warning(
                "blue_agent_api_failure",
                extra={"source": source_name, "value": value, "error": str(exc)},
            )
            if sleep_after > 0:
                time.sleep(sleep_after)
            return None
