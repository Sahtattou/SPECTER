from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from app.clients.go_api_client import GoAPIClient
from app.schemas import BlueAnalysisResponse
from app.tools.event_tools import get_recent_events


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def run_blue_analyst_chain(client: GoAPIClient, limit: int = 100) -> BlueAnalysisResponse:
    events = get_recent_events(client, limit=limit)
    if not events:
        return BlueAnalysisResponse(
            summary="No events available from the Go API for analysis.",
            total_events=0,
            by_threat_level={},
            top_iocs=[],
            recommended_actions=["Confirm collector and worker services are running."],
        )

    threat_counts = Counter((event.get("threat_level") or "UNKNOWN").upper() for event in events)
    sorted_events: List[Dict[str, Any]] = sorted(
        events,
        key=lambda event: _to_float(event.get("composite_score", 0.0)),
        reverse=True,
    )

    top_iocs = []
    for event in sorted_events[:5]:
        ioc_value = str(event.get("ioc_value") or event.get("raw_value") or "unknown")
        threat_level = str(event.get("threat_level") or "UNKNOWN").upper()
        score = _to_float(event.get("composite_score", 0.0))
        top_iocs.append(f"{ioc_value} ({threat_level}, score={score:.1f})")

    critical = threat_counts.get("CRITICAL", 0)
    high = threat_counts.get("HIGH", 0)
    summary = (
        f"Analyzed {len(events)} events. "
        f"Critical={critical}, High={high}, "
        f"Top IOC={top_iocs[0] if top_iocs else 'none'}."
    )

    recommendations = [
        "Investigate all CRITICAL IOCs within the first response window.",
        "Correlate top-scored IP/domain IOCs in SIEM for active detections.",
        "Review quarantined records to confirm poison detection quality.",
    ]

    return BlueAnalysisResponse(
        summary=summary,
        total_events=len(events),
        by_threat_level=dict(threat_counts),
        top_iocs=top_iocs,
        recommended_actions=recommendations,
    )
