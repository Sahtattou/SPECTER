from __future__ import annotations

from typing import Any, Dict

from app.clients.go_api_client import GoAPIClient


def submit_synthetic_event(client: GoAPIClient, payload: Dict[str, Any]) -> Dict[str, Any]:
    return client.submit_synthetic_event(payload)
