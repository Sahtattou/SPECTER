from __future__ import annotations

from typing import Any


def detected_status(value: Any) -> str:
    return "CAUGHT" if value == 1 else ("MISSED" if value == 0 else "PENDING")


def origin_label(event: dict[str, Any]) -> str:
    return (
        "Injected simulation" if bool(event.get("is_synthetic")) else "Real telemetry"
    )


def verdict_label(event: dict[str, Any]) -> str:
    stage = str(event.get("pipeline_stage") or "")
    poison_detected = event.get("poison_detected")
    is_synthetic = bool(event.get("is_synthetic"))
    if stage == "quarantined" and poison_detected is True:
        return "Detected (Quarantined)"
    if stage in {"validated", "scored"} and poison_detected is False:
        return "Passed Validation"
    if is_synthetic and poison_detected is False:
        return "Missed Injection"
    return "Needs Review"


def status_css_class(status: str) -> str:
    return (
        "status-caught"
        if status == "CAUGHT"
        else ("status-missed" if status == "MISSED" else "status-pending")
    )
