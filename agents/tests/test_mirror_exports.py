from __future__ import annotations

import json
from pathlib import Path

from app.adversarial.service import AdversarialMirrorService
from app.exports import export_snapshot_report, export_snapshot_stix


def _seed_service(service: AdversarialMirrorService) -> None:
    service.ingest_real_ioc(
        {
            "ioc_uuid": "evt-sync-1",
            "raw_value": "sync-example.com",
            "ioc_type": "domain",
            "source_name": "otx",
            "source_url": "https://otx.alienvault.com",
            "source_query": "sync-example.com",
            "raw_evidence": {"confidence": "high"},
            "collected_at": "2026-03-23T12:00:00Z",
            "corroboration_count": 2,
            "open_ports": [],
            "asn": None,
            "pipeline_stage": "validated",
            "is_synthetic": False,
        }
    )
    service.trigger_injection("GHOST_DOMAIN")


def test_mirror_stix_export_aligns_with_snapshot_counts(tmp_path) -> None:
    db_path = str(tmp_path / "mirror_exports_stix.db")
    service = AdversarialMirrorService(
        db_path=db_path,
        red_agent_interval_seconds=9999,
        red_max_ratio=1.0,
        min_real_events_before_auto_red=0,
        go_sync_interval_seconds=15,
        go_sync_batch_limit=20,
        go_sync_on_startup=False,
        go_client=None,
    )
    _seed_service(service)

    snapshot = service.get_dashboard_snapshot(event_limit=50, injection_limit=50)
    path, count = export_snapshot_stix(snapshot)

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["type"] == "bundle"
    assert data["x_specter_snapshot_generated_at"] == snapshot["snapshot_generated_at"]
    assert count == len(snapshot["events"])
    assert len(data["objects"]) == len(snapshot["events"])


def test_mirror_report_export_contains_snapshot_metadata(tmp_path) -> None:
    db_path = str(tmp_path / "mirror_exports_report.db")
    service = AdversarialMirrorService(
        db_path=db_path,
        red_agent_interval_seconds=9999,
        red_max_ratio=1.0,
        min_real_events_before_auto_red=0,
        go_sync_interval_seconds=15,
        go_sync_batch_limit=20,
        go_sync_on_startup=False,
        go_client=None,
    )
    _seed_service(service)

    snapshot = service.get_dashboard_snapshot(event_limit=50, injection_limit=50)
    path, count = export_snapshot_report(snapshot)

    content = Path(path).read_text(encoding="utf-8")
    assert "%PDF-1.4" in content
    assert "Snapshot Generated At:" in content
    assert "Snapshot ID:" in content
    assert count == len(snapshot["events"])
