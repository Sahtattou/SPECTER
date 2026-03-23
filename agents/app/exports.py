from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.chains.red_injector_chain import ATTACK_TYPES

ATTACK_PATTERN_BY_TYPE: dict[str, str] = {
    "REPUTATION_LAUNDERING": "Synthetic reputation laundering attempt",
    "GHOST_DOMAIN": "Synthetic ghost domain IOC resembling phishing setup",
    "TTP_MISMATCH": "Synthetic tactic mismatch artifact",
    "TIMESTAMP_MANIPULATION": "Synthetic historical timestamp manipulation IOC",
}
for _attack in ATTACK_TYPES:
    ATTACK_PATTERN_BY_TYPE.setdefault(_attack, "Mirror IOC snapshot indicator")

SCO_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | str | None) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return _utc_now().isoformat()


def _score_to_int(score: Any) -> int:
    if isinstance(score, (int, float)):
        if score < 0:
            return 0
        if score > 100:
            return 100
        return int(score)
    return 0


def _artifact_dir(subdir: str) -> Path:
    root = Path("artifacts") / subdir
    root.mkdir(parents=True, exist_ok=True)
    return root


def _snapshot_id(snapshot_generated_at: str, metrics: Dict[str, Any]) -> str:
    total_events = int(metrics.get("total_events", 0))
    total_injections = int(metrics.get("total_injections", 0))
    payload = f"{snapshot_generated_at}|{total_events}|{total_injections}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, payload))


def export_snapshot_stix(snapshot: Dict[str, Any]) -> tuple[str, int]:
    snapshot_generated_at = _iso(snapshot.get("snapshot_generated_at"))
    metrics = snapshot.get("metrics") or {}
    events: List[Dict[str, Any]] = list(snapshot.get("events") or [])

    bundle_ts = _utc_now().strftime("%Y%m%d_%H%M%S")
    out_dir = _artifact_dir("stix")
    out_path = out_dir / f"specter_mirror_snapshot_{bundle_ts}.stix.json"

    snapshot_uuid = _snapshot_id(snapshot_generated_at, metrics)
    bundle_id = f"bundle--{snapshot_uuid}"

    objects: List[Dict[str, Any]] = []
    for event in events:
        ioc_type = str(event.get("ioc_type") or "domain").strip().lower()
        raw_value = str(event.get("raw_value") or "").strip()
        ioc_uuid = str(event.get("ioc_uuid") or "").strip()
        if not raw_value or not ioc_uuid:
            continue

        created = _iso(
            event.get("created_at")
            or event.get("collected_at")
            or snapshot_generated_at
        )
        modified = _iso(
            event.get("updated_at")
            or event.get("collected_at")
            or snapshot_generated_at
        )
        indicator_uuid = str(
            uuid.uuid5(SCO_NAMESPACE, f"{ioc_type}:{raw_value}:{ioc_uuid}")
        )

        if ioc_type == "ip":
            pattern = f"[ipv4-addr:value = '{raw_value}']"
        elif ioc_type == "url":
            pattern = f"[url:value = '{raw_value}']"
        else:
            pattern = f"[domain-name:value = '{raw_value}']"

        attack_type = str(event.get("poison_attack_type") or "").strip()
        labels = [
            str(event.get("threat_level") or "unknown").lower(),
            "specter",
            "mirror-snapshot",
        ]
        if attack_type:
            labels.append(f"attack:{attack_type.lower()}")

        objects.append(
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": f"indicator--{indicator_uuid}",
                "created": created,
                "modified": modified,
                "name": raw_value,
                "description": ATTACK_PATTERN_BY_TYPE.get(
                    attack_type, "Mirror IOC snapshot indicator"
                ),
                "pattern_type": "stix",
                "pattern": pattern,
                "confidence": _score_to_int(event.get("composite_score")),
                "labels": labels,
                "x_specter_pipeline_stage": str(
                    event.get("pipeline_stage") or "raw_ingest"
                ),
                "x_specter_source_name": str(event.get("source_name") or "unknown"),
                "x_specter_snapshot_generated_at": snapshot_generated_at,
                "x_specter_snapshot_id": snapshot_uuid,
            }
        )

    bundle = {
        "type": "bundle",
        "id": bundle_id,
        "objects": objects,
        "x_specter_snapshot_generated_at": snapshot_generated_at,
        "x_specter_snapshot_id": snapshot_uuid,
        "x_specter_content_hash_basis": f"{snapshot_generated_at}|{len(events)}|{int(metrics.get('total_events', 0))}",
        "x_specter_metrics": metrics,
    }

    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return str(out_path), len(objects)


def export_snapshot_report(snapshot: Dict[str, Any]) -> tuple[str, int]:
    snapshot_generated_at = _iso(snapshot.get("snapshot_generated_at"))
    metrics = snapshot.get("metrics") or {}
    events: List[Dict[str, Any]] = list(snapshot.get("events") or [])
    injections: List[Dict[str, Any]] = list(snapshot.get("injections") or [])

    report_ts = _utc_now().strftime("%Y%m%d_%H%M%S")
    out_dir = _artifact_dir("reports")
    out_path = out_dir / f"specter_mirror_snapshot_{report_ts}.pdf"

    top_events = sorted(
        events,
        key=lambda item: float(item.get("composite_score") or 0.0),
        reverse=True,
    )[:8]

    snapshot_uuid = _snapshot_id(snapshot_generated_at, metrics)
    lines = [
        "SPECTER Mirror Snapshot Report",
        "",
        f"Snapshot Generated At: {snapshot_generated_at}",
        f"Snapshot ID: {snapshot_uuid}",
        f"Total Events: {int(metrics.get('total_events', 0))}",
        f"Validated Events: {int(metrics.get('validated_events', 0))}",
        f"Quarantined Events: {int(metrics.get('quarantined_events', 0))}",
        f"Total Injections: {int(metrics.get('total_injections', 0))}",
        f"Caught Injections: {int(metrics.get('caught_injections', 0))}",
        f"Catch Rate: {float(metrics.get('catch_rate_percent', 0.0)):.2f}%",
        f"Real Events: {int(metrics.get('real_events', 0))}",
        f"Snapshot Events Returned: {len(events)}",
        f"Snapshot Injections Returned: {len(injections)}",
        f"Content Hash Basis: {snapshot_generated_at}|{len(events)}|{len(injections)}",
        "",
        "Top IOC Feed Entries (by score):",
    ]

    for event in top_events:
        raw = str(event.get("raw_value") or "n/a")
        ioc_type = str(event.get("ioc_type") or "unknown")
        stage = str(event.get("pipeline_stage") or "raw_ingest")
        score = float(event.get("composite_score") or 0.0)
        verdict = "review"
        poison_detected = event.get("poison_detected")
        if stage == "quarantined" and poison_detected is True:
            verdict = "detected"
        elif stage in {"validated", "scored"} and poison_detected is False:
            verdict = "passed"
        elif event.get("is_synthetic") and poison_detected is False:
            verdict = "missed"
        lines.append(
            f"- {raw} [{ioc_type}] stage={stage} verdict={verdict} score={score:.1f}"
        )

    report_text = "\n".join(lines)
    pdf_like = (
        f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n% {report_text}\n%%EOF\n"
    )
    out_path.write_text(pdf_like, encoding="utf-8")
    return str(out_path), len(events)


def ensure_artifacts_root() -> str:
    root = Path("artifacts")
    root.mkdir(parents=True, exist_ok=True)
    return os.fspath(root)
