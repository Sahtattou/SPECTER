from __future__ import annotations

from typing import Any

import requests

from .config import DashboardConfig


def _require_dict_payload(payload: Any, endpoint: str) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise ValueError(
        f"Expected JSON object from {endpoint}, got {type(payload).__name__}"
    )


def get_agent_json(config: DashboardConfig, path: str) -> dict[str, Any]:
    response = requests.get(f"{config.agent_api_base}{path}", timeout=10)
    response.raise_for_status()
    payload = response.json()
    return _require_dict_payload(payload, f"agent:{path}")


def get_go_json(config: DashboardConfig, path: str) -> dict[str, Any]:
    response = requests.get(f"{config.go_api_base}{path}", timeout=10)
    response.raise_for_status()
    payload = response.json()
    return _require_dict_payload(payload, f"go:{path}")


def post_agent_json(
    config: DashboardConfig, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    response = requests.post(
        f"{config.agent_api_base}{path}", json=payload or {}, timeout=10
    )
    response.raise_for_status()
    result = response.json()
    return _require_dict_payload(result, f"agent:{path}")


def post_go_json(
    config: DashboardConfig, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    response = requests.post(
        f"{config.go_api_base}{path}", json=payload or {}, timeout=20
    )
    response.raise_for_status()
    result = response.json()
    return _require_dict_payload(result, f"go:{path}")
