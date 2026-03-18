from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from app.adversarial.blue_agent import BlueAgent
from app.adversarial.detector import Detector
from app.adversarial.models import IOCEnvelope
from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.red_agent import ATTACK_TYPES, RedAgent
from app.adversarial.storage import AdversarialStorage

logger = logging.getLogger(__name__)


class AdversarialMirrorService:
    def __init__(
        self,
        *,
        db_path: str,
        red_agent_interval_seconds: int,
        source_clients: Optional[Dict[str, Callable[[str], Dict[str, Any]]]] = None,
    ) -> None:
        self.storage = AdversarialStorage(db_path=db_path)
        self.queue = SharedQueueManager()
        self.blue_agent = BlueAgent(source_clients=source_clients or {})
        self.red_agent = RedAgent(
            queue_manager=self.queue,
            storage=self.storage,
            interval_seconds=red_agent_interval_seconds,
        )
        self.detector = Detector(queue_manager=self.queue, storage=self.storage)

    def start(self) -> None:
        self.detector.start()
        self.red_agent.start()

    def stop(self) -> None:
        self.red_agent.stop()
        self.detector.stop()

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
        return metrics

    def get_injection_activity(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.storage.get_injections(limit=limit)
