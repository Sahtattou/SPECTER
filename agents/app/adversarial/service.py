from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from app.adversarial.blue_agent import BlueAgent
from app.adversarial.detector import Detector
from app.adversarial.models import IOCEnvelope
from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.red_agent import ATTACK_TYPES, RedAgent
from app.adversarial.storage import AdversarialStorage
from app.clients.go_api_client import GoAPIClient

logger = logging.getLogger(__name__)


class AdversarialMirrorService:
    def __init__(
        self,
        *,
        db_path: str,
        red_agent_interval_seconds: int,
        red_max_ratio: float,
        min_real_events_before_auto_red: int,
        go_sync_interval_seconds: int,
        go_sync_batch_limit: int,
        go_sync_on_startup: bool,
        go_client: Optional[GoAPIClient] = None,
        source_clients: Optional[Dict[str, Callable[[str], Dict[str, Any]]]] = None,
    ) -> None:
        self.storage = AdversarialStorage(db_path=db_path)
        self.queue = SharedQueueManager()
        self.blue_agent = BlueAgent(source_clients=source_clients or {})
        self.go_client = go_client
        self.red_max_ratio = max(0.1, float(red_max_ratio))
        self.min_real_events_before_auto_red = max(
            0, int(min_real_events_before_auto_red)
        )
        self.go_sync_interval_seconds = max(3, int(go_sync_interval_seconds))
        self.go_sync_batch_limit = max(1, min(50, int(go_sync_batch_limit)))
        self.go_sync_on_startup = bool(go_sync_on_startup)

        self._go_sync_thread: Optional[threading.Thread] = None
        self._go_sync_stop = threading.Event()
        self._seen_real_event_ids: set[str] = set()
        self._auto_red_last_allowed: Optional[bool] = None
        self._auto_red_last_reason: str = "not-evaluated"
        self._auto_red_last_ratio: float = 0.0

        self.red_agent = RedAgent(
            queue_manager=self.queue,
            storage=self.storage,
            interval_seconds=red_agent_interval_seconds,
            should_inject=self._should_allow_auto_red_injection,
        )
        self.detector = Detector(queue_manager=self.queue, storage=self.storage)

    def start(self) -> None:
        self._warm_seen_event_ids()
        self.detector.start()
        self.red_agent.start()
        self._start_go_sync()

    def stop(self) -> None:
        self.red_agent.stop()
        self.detector.stop()
        self._stop_go_sync()

    def ingest_real_ioc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        envelope = IOCEnvelope.from_dict(payload)
        envelope.is_synthetic = False
        envelope.poison_attack_type = None
        envelope.poison_detected = None
        envelope.detection_rule = None
        enriched = self.blue_agent.enrich(envelope)
        self.storage.save_event(enriched)
        self.storage.record_pipeline_run_values([enriched])
        self.queue.enqueue(enriched)
        if envelope.ioc_uuid:
            self._seen_real_event_ids.add(envelope.ioc_uuid)
        return enriched.to_dict()

    def trigger_injection(self, attack_type: Optional[str] = None) -> Dict[str, Any]:
        if attack_type and attack_type not in ATTACK_TYPES:
            raise ValueError(f"unsupported attack_type '{attack_type}'")
        envelope = self.red_agent.inject_now(attack_type=attack_type)
        return {
            "submitted": True,
            "attack_type": envelope.poison_attack_type,
            "ioc_uuid": envelope.ioc_uuid,
            "raw_value": envelope.raw_value,
            "pipeline_stage": envelope.pipeline_stage,
        }

    def get_events(
        self, limit: int = 100, stage: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        events = self.storage.get_recent_events(limit=limit)
        if stage:
            return [
                event for event in events if str(event.get("pipeline_stage")) == stage
            ]
        return events

    def get_metrics(self) -> Dict[str, Any]:
        metrics = self.storage.get_metrics()
        metrics["queue_size"] = self.queue.size()
        total = int(metrics.get("total_events", 0))
        total_injections = int(metrics.get("total_injections", 0))
        real_events = max(total - total_injections, 0)
        ratio = (
            0.0 if real_events == 0 else round(total_injections / float(real_events), 3)
        )
        metrics["real_events"] = real_events
        metrics["red_blue_ratio"] = ratio
        metrics["red_max_ratio"] = self.red_max_ratio
        metrics["min_real_events_before_auto_red"] = (
            self.min_real_events_before_auto_red
        )
        metrics["auto_red_last_allowed"] = self._auto_red_last_allowed
        metrics["auto_red_last_reason"] = self._auto_red_last_reason
        metrics["auto_red_last_ratio"] = round(self._auto_red_last_ratio, 3)
        return metrics

    def get_injection_activity(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.storage.get_injections(limit=limit)

    def _should_allow_auto_red_injection(self) -> bool:
        metrics = self.storage.get_metrics()
        total = int(metrics.get("total_events", 0))
        total_injections = int(metrics.get("total_injections", 0))
        real_events = max(total - total_injections, 0)

        if real_events < self.min_real_events_before_auto_red:
            self._auto_red_last_allowed = False
            self._auto_red_last_reason = "waiting-for-real-baseline"
            self._auto_red_last_ratio = (
                0.0 if real_events == 0 else total_injections / float(real_events)
            )
            return False

        if real_events == 0:
            self._auto_red_last_allowed = False
            self._auto_red_last_reason = "no-real-events"
            self._auto_red_last_ratio = 0.0
            return False

        current_ratio = total_injections / float(real_events)
        self._auto_red_last_ratio = current_ratio
        allowed = current_ratio < self.red_max_ratio
        self._auto_red_last_allowed = allowed
        if allowed:
            self._auto_red_last_reason = "within-ratio"
        else:
            self._auto_red_last_reason = "ratio-throttled"
        return allowed

    def _start_go_sync(self) -> None:
        if self.go_client is None:
            return
        if self._go_sync_thread and self._go_sync_thread.is_alive():
            return

        self._go_sync_stop.clear()
        self._go_sync_thread = threading.Thread(
            target=self._go_sync_loop,
            name="specter-go-blue-sync",
            daemon=True,
        )
        self._go_sync_thread.start()

    def _stop_go_sync(self) -> None:
        self._go_sync_stop.set()

    def _go_sync_loop(self) -> None:
        first_cycle = True
        while not self._go_sync_stop.is_set():
            if first_cycle and not self.go_sync_on_startup:
                first_cycle = False
                if self._go_sync_stop.wait(self.go_sync_interval_seconds):
                    return
                continue
            first_cycle = False
            try:
                self._sync_go_events_once()
            except Exception as exc:
                logger.warning("go_blue_sync_failed", extra={"error": str(exc)})
            if self._go_sync_stop.wait(self.go_sync_interval_seconds):
                return

    def _sync_go_events_once(self) -> None:
        if self.go_client is None:
            return
        recent = self.go_client.get_recent_events(limit=self.go_sync_batch_limit)
        for event in recent:
            event_id = str(event.get("event_id") or "").strip()
            if not event_id or event_id in self._seen_real_event_ids:
                continue
            if bool(event.get("is_synthetic")):
                self._seen_real_event_ids.add(event_id)
                continue

            payload = {
                "ioc_uuid": event_id,
                "raw_value": event.get("ioc_value") or event.get("raw_value") or "",
                "ioc_type": event.get("ioc_type") or "unknown",
                "source_name": event.get("source_name") or "go_pipeline",
                "source_url": event.get("source_url"),
                "source_query": event.get("source_query"),
                "raw_evidence": event.get("raw_evidence") or {},
                "collected_at": event.get("collected_at") or "",
                "corroboration_count": event.get("corroboration_count") or 1,
                "open_ports": event.get("open_ports") or [],
                "asn": event.get("asn"),
                "pipeline_stage": "raw_ingest",
                "is_synthetic": False,
            }
            self.ingest_real_ioc(payload)
            self._seen_real_event_ids.add(event_id)

    def _warm_seen_event_ids(self) -> None:
        events = self.storage.get_recent_events(limit=1000)
        for event in events:
            ioc_uuid = str(event.get("ioc_uuid") or "").strip()
            if ioc_uuid:
                self._seen_real_event_ids.add(ioc_uuid)
