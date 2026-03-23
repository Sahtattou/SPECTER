from __future__ import annotations

from app.adversarial.service import AdversarialMirrorService


class _PipelineMetricsClient:
    def __init__(self, total_events: int) -> None:
        self.total_events = total_events

    def get_recent_events(self, limit: int = 50):
        return []

    def get_pipeline_metrics(self):
        return {
            "total_events": self.total_events,
            "scored_count": 0,
            "quarantined_count": 0,
        }


def test_dashboard_snapshot_is_consistent_single_payload(tmp_path) -> None:
    db_path = str(tmp_path / "dashboard_snapshot.db")
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

    service.ingest_real_ioc(
        {
            "ioc_uuid": "evt-1",
            "raw_value": "example.com",
            "ioc_type": "domain",
            "source_name": "otx",
            "source_url": "https://otx.alienvault.com",
            "source_query": "example.com",
            "raw_evidence": {},
            "collected_at": "2026-03-23T12:00:00Z",
            "corroboration_count": 2,
            "open_ports": [],
            "asn": None,
            "pipeline_stage": "validated",
            "is_synthetic": False,
        }
    )

    service.trigger_injection("GHOST_DOMAIN")
    snapshot = service.get_dashboard_snapshot(event_limit=50, injection_limit=50)

    assert isinstance(snapshot.get("snapshot_generated_at"), str)
    metrics = snapshot["metrics"]
    events = snapshot["events"]
    injections = snapshot["injections"]

    assert metrics["total_events"] == len(events)
    assert metrics["total_injections"] == len(injections)


def test_dashboard_snapshot_uses_pipeline_total_events_when_available(tmp_path) -> None:
    db_path = str(tmp_path / "dashboard_snapshot_pipeline_metrics.db")
    service = AdversarialMirrorService(
        db_path=db_path,
        red_agent_interval_seconds=9999,
        red_max_ratio=1.0,
        min_real_events_before_auto_red=0,
        go_sync_interval_seconds=15,
        go_sync_batch_limit=20,
        go_sync_on_startup=False,
        go_client=_PipelineMetricsClient(total_events=77),
    )

    service.ingest_real_ioc(
        {
            "ioc_uuid": "evt-pipeline-total",
            "raw_value": "pipeline-total.example",
            "ioc_type": "domain",
            "source_name": "otx",
            "source_url": "https://otx.alienvault.com",
            "source_query": "pipeline-total.example",
            "raw_evidence": {},
            "collected_at": "2026-03-23T12:00:00Z",
            "corroboration_count": 2,
            "open_ports": [],
            "asn": None,
            "pipeline_stage": "validated",
            "is_synthetic": False,
        }
    )

    snapshot = service.get_dashboard_snapshot(event_limit=50, injection_limit=50)
    metrics = snapshot["metrics"]

    assert metrics["mirror_total_events"] == 1
    assert metrics["pipeline_total_events"] == 77
    assert metrics["total_events"] == 77


def test_dashboard_snapshot_total_events_advances_with_pipeline_runs(tmp_path) -> None:
    db_path = str(tmp_path / "dashboard_snapshot_pipeline_runs.db")
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

    payload = {
        "ioc_uuid": "evt-pipeline-run-1",
        "raw_value": "pipeline-run.example",
        "ioc_type": "domain",
        "source_name": "otx",
        "source_url": "https://otx.alienvault.com",
        "source_query": "pipeline-run.example",
        "raw_evidence": {},
        "collected_at": "2026-03-23T12:00:00Z",
        "corroboration_count": 2,
        "open_ports": [],
        "asn": None,
        "pipeline_stage": "validated",
        "is_synthetic": False,
    }
    service.ingest_real_ioc(payload)

    payload_repeat = dict(payload)
    payload_repeat["collected_at"] = "2026-03-23T12:01:00Z"
    service.ingest_real_ioc(payload_repeat)

    snapshot = service.get_dashboard_snapshot(event_limit=50, injection_limit=50)
    metrics = snapshot["metrics"]

    assert metrics["mirror_total_events"] == 1
    assert metrics["pipeline_run_total"] == 2
    assert metrics["total_events"] == 2
