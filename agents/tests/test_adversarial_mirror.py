from __future__ import annotations

import time

from app.adversarial.service import AdversarialMirrorService
from app.adversarial.detector import Detector
from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.red_agent import ATTACK_TYPES, RedAgent
from app.adversarial.storage import AdversarialStorage


def test_manual_injections_are_caught(tmp_path) -> None:
    db_path = str(tmp_path / "adversarial_test.db")
    storage = AdversarialStorage(db_path=db_path)
    queue = SharedQueueManager()
    detector = Detector(queue_manager=queue, storage=storage)
    red = RedAgent(queue_manager=queue, storage=storage, interval_seconds=9999)

    detector.start()
    try:
        for attack in ATTACK_TYPES:
            red.inject_now(attack_type=attack)

        deadline = time.time() + 5.0
        while time.time() < deadline:
            injections = storage.get_injections(limit=20)
            if len(injections) >= len(ATTACK_TYPES) and all(
                item.get("detected") == 1 for item in injections[: len(ATTACK_TYPES)]
            ):
                break
            time.sleep(0.1)

        injections = storage.get_injections(limit=20)
        assert len(injections) >= len(ATTACK_TYPES)
        assert all(
            item.get("detected") == 1 for item in injections[: len(ATTACK_TYPES)]
        )
    finally:
        detector.stop()


def test_red_agent_auto_loop_respects_should_inject_gate(tmp_path) -> None:
    db_path = str(tmp_path / "adversarial_gate.db")
    storage = AdversarialStorage(db_path=db_path)
    queue = SharedQueueManager()

    red = RedAgent(
        queue_manager=queue,
        storage=storage,
        interval_seconds=1,
        should_inject=lambda: False,
    )
    red.start()
    try:
        time.sleep(1.6)
        injections = storage.get_injections(limit=5)
        assert len(injections) == 0
    finally:
        red.stop()


class _FakeGoClient:
    def __init__(self, events):
        self._events = events

    def set_events(self, events):
        self._events = events

    def get_recent_events(self, limit: int = 50):
        return self._events[:limit]

    def get_pipeline_metrics(self):
        return {"total_events": len(self._events)}


def test_go_sync_updates_existing_event_when_collected_at_changes(tmp_path) -> None:
    db_path = str(tmp_path / "adversarial_sync.db")
    fake = _FakeGoClient(
        [
            {
                "event_id": "evt-1",
                "ioc_value": "alpha.example",
                "ioc_type": "domain",
                "source_name": "otx",
                "collected_at": "2026-03-22T10:00:00Z",
                "corroboration_count": 1,
                "is_synthetic": False,
            }
        ]
    )

    service = AdversarialMirrorService(
        db_path=db_path,
        red_agent_interval_seconds=9999,
        red_max_ratio=1.0,
        min_real_events_before_auto_red=0,
        go_sync_interval_seconds=15,
        go_sync_batch_limit=20,
        go_sync_on_startup=True,
        go_client=fake,
    )

    service._sync_go_events_once()
    first = service.get_events(limit=1)[0]
    assert first["collected_at"] == "2026-03-22T10:00:00Z"

    fake.set_events(
        [
            {
                "event_id": "evt-1",
                "ioc_value": "alpha.example",
                "ioc_type": "domain",
                "source_name": "otx",
                "collected_at": "2026-03-22T10:05:00Z",
                "corroboration_count": 1,
                "is_synthetic": False,
            }
        ]
    )
    service._sync_go_events_once()

    second = service.get_events(limit=1)[0]
    assert second["ioc_uuid"] == "evt-1"
    assert second["collected_at"] == "2026-03-22T10:05:00Z"


def test_go_sync_preserves_scoring_and_quarantine_fields(tmp_path) -> None:
    db_path = str(tmp_path / "adversarial_sync_scoring.db")
    fake = _FakeGoClient(
        [
            {
                "event_id": "evt-score-1",
                "ioc_value": "198.51.100.44",
                "ioc_type": "ip",
                "source_name": "go_pipeline",
                "collected_at": "2026-03-22T10:00:00Z",
                "corroboration_count": 3,
                "is_synthetic": False,
                "pipeline_stage": "quarantined",
                "composite_score": 0.0,
                "threat_level": "low",
                "days_to_attack": "8+",
                "score_breakdown": {"base": 20, "penalty_poison": -100},
                "poison_detected": "true",
                "detection_rule": "SUSPICIOUS_TIMESTAMP",
            }
        ]
    )

    service = AdversarialMirrorService(
        db_path=db_path,
        red_agent_interval_seconds=9999,
        red_max_ratio=1.0,
        min_real_events_before_auto_red=0,
        go_sync_interval_seconds=15,
        go_sync_batch_limit=20,
        go_sync_on_startup=True,
        go_client=fake,
    )

    service._sync_go_events_once()

    event = service.get_events(limit=1)[0]
    assert event["ioc_uuid"] == "evt-score-1"
    assert event["pipeline_stage"] == "quarantined"
    assert event["composite_score"] == 0.0
    assert event["threat_level"] == "low"
    assert event["days_to_attack_estimate"] == "8+"
    assert event["score_breakdown"] == {"base": 20, "penalty_poison": -100}
    assert event["poison_detected"] is True
    assert event["detection_rule"] == "SUSPICIOUS_TIMESTAMP"
