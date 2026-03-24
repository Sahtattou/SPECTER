from __future__ import annotations

import random

from app.adversarial.queue_manager import SharedQueueManager
from app.adversarial.red_agent import RedAgent
from app.adversarial.storage import AdversarialStorage


def _create_agent(tmp_path, *, rng_seed: int = 7) -> RedAgent:
    storage = AdversarialStorage(db_path=str(tmp_path / "red_adaptive.db"))
    queue = SharedQueueManager()
    return RedAgent(
        queue_manager=queue,
        storage=storage,
        interval_seconds=9999,
        rng=random.Random(rng_seed),
    )


def test_adaptive_weights_prioritize_recent_misses_over_hits(tmp_path) -> None:
    agent = _create_agent(tmp_path)
    injections = [
        {"attack_type": "GHOST_DOMAIN", "detected": 1},
        {"attack_type": "GHOST_DOMAIN", "detected": 1},
        {"attack_type": "GHOST_DOMAIN", "detected": 0},
        {"attack_type": "REPUTATION_LAUNDERING", "detected": 0},
        {"attack_type": "REPUTATION_LAUNDERING", "detected": 0},
        {"attack_type": "REPUTATION_LAUNDERING", "detected": 0},
        {"attack_type": "TTP_MISMATCH", "detected": None},
        {"attack_type": "TIMESTAMP_MANIPULATION", "detected": 1},
    ]

    weights, performance = agent._compute_adaptive_weights(injections)

    assert performance["REPUTATION_LAUNDERING"]["misses"] > 0
    assert weights["REPUTATION_LAUNDERING"] > weights["GHOST_DOMAIN"]
    assert weights["REPUTATION_LAUNDERING"] > weights["TIMESTAMP_MANIPULATION"]


def test_adaptive_selection_inject_now_embeds_strategy_metadata(tmp_path) -> None:
    agent = _create_agent(tmp_path, rng_seed=11)

    for index in range(5):
        ioc_uuid = f"adaptive-ttp-{index}"
        agent.storage.log_injection(
            attack_type="TTP_MISMATCH",
            raw_value="198.51.100.77",
            ioc_uuid=ioc_uuid,
        )
        agent.storage.update_injection_detection(
            ioc_uuid=ioc_uuid,
            detected=False,
            detection_rule=None,
        )

    envelope = agent.inject_now()

    strategy = envelope.raw_evidence.get("red_strategy")
    assert isinstance(strategy, dict)
    assert strategy.get("mode") == "adaptive"
    assert isinstance(strategy.get("weights"), dict)
    assert strategy.get("selected_attack") in strategy["weights"]
    assert strategy["weights"]["TTP_MISMATCH"] >= strategy["weights"]["GHOST_DOMAIN"]


def test_normalize_detected_handles_strings_and_nulls(tmp_path) -> None:
    agent = _create_agent(tmp_path)

    assert agent._normalize_detected("true") is True
    assert agent._normalize_detected("false") is False
    assert agent._normalize_detected("1") is True
    assert agent._normalize_detected("0") is False
    assert agent._normalize_detected("null") is None
    assert agent._normalize_detected(None) is None
