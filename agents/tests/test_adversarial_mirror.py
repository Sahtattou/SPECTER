from __future__ import annotations

import time

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
