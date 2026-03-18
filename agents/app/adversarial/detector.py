from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.adversarial.models import IOCEnvelope
from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.storage import AdversarialStorage

logger = logging.getLogger(__name__)

CDN_BRANDS = ["cloudflare", "akamai", "fastly", "amazon", "azure", "google"]
C2_PORTS = [50050, 40056, 8888, 4444]


class Detector:
    def __init__(
        self, queue_manager: SharedQueueManager, storage: AdversarialStorage
    ) -> None:
        self.queue_manager = queue_manager
        self.storage = storage
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="specter-detector", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def evaluate(self, envelope: IOCEnvelope) -> IOCEnvelope:
        decision, rule = self._apply_rules(envelope)
        if decision == "quarantined":
            envelope.poison_detected = True
            envelope.detection_rule = rule
            envelope.pipeline_stage = "quarantined"
        else:
            envelope.poison_detected = False
            envelope.detection_rule = None
            envelope.pipeline_stage = "validated"

        self.storage.save_event(envelope)

        if envelope.is_synthetic:
            self.storage.update_injection_detection(
                ioc_uuid=envelope.ioc_uuid,
                detected=bool(envelope.poison_detected),
                detection_rule=envelope.detection_rule,
            )

        return envelope

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            envelope = self.queue_manager.dequeue(timeout_seconds=2.0)
            if envelope is None:
                continue

            try:
                self.evaluate(envelope)
            except Exception as exc:
                logger.exception(
                    "detector_processing_error",
                    extra={"ioc_uuid": envelope.ioc_uuid, "error": str(exc)},
                )
            finally:
                self.queue_manager.task_done()

    def _apply_rules(self, envelope: IOCEnvelope) -> Tuple[str, Optional[str]]:
        if self._rule_single_source_fresh_domain_or_laundered_ip(envelope):
            return "quarantined", "SINGLE_SOURCE_FRESH_DOMAIN"

        if self._rule_ttp_banner_mismatch(envelope):
            return "quarantined", "TTP_BANNER_MISMATCH"

        if self._rule_suspicious_timestamp(envelope):
            return "quarantined", "SUSPICIOUS_TIMESTAMP"

        return "validated", None

    @staticmethod
    def _rule_single_source_fresh_domain_or_laundered_ip(envelope: IOCEnvelope) -> bool:
        corroboration = int(envelope.corroboration_count or 0)
        domain_age = envelope.domain_age_days
        if corroboration <= 1 and domain_age is not None and int(domain_age) < 7:
            return True

        if envelope.ioc_type == "ip" and corroboration <= 1:
            return True

        return False

    def _rule_suspicious_timestamp(self, envelope: IOCEnvelope) -> bool:
        collected_at = self._parse_iso_datetime(envelope.collected_at)
        if collected_at is None:
            return False

        now = datetime.now(timezone.utc)
        if now - collected_at <= timedelta(days=20):
            return False

        return not self.storage.has_historical_raw_value_before_today(
            envelope.raw_value
        )

    @staticmethod
    def _rule_ttp_banner_mismatch(envelope: IOCEnvelope) -> bool:
        if envelope.ioc_type != "ip":
            return False

        open_ports = [int(port) for port in (envelope.open_ports or [])]
        has_c2_port = any(port in C2_PORTS for port in open_ports)
        if not has_c2_port:
            return False

        evidence_string = Detector._evidence_to_search_string(envelope.raw_evidence)
        has_brand = any(brand in evidence_string for brand in CDN_BRANDS)
        return has_brand

    @staticmethod
    def _evidence_to_search_string(raw_evidence: Dict[str, object]) -> str:
        try:
            return json.dumps(raw_evidence).lower()
        except (TypeError, ValueError):
            return str(raw_evidence).lower()

    @staticmethod
    def _parse_iso_datetime(value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except (TypeError, ValueError):
            return None
