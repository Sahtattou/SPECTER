from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.go_api_client import GoAPIClient


def get_recent_events(client: GoAPIClient, limit: int = 100, stage: Optional[str] = None) -> List[Dict[str, Any]]:
    return client.get_recent_events(limit=limit, stage=stage)


def get_pipeline_metrics(client: GoAPIClient) -> Dict[str, Any]:
    return client.get_pipeline_metrics()
