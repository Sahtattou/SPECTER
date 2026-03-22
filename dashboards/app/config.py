from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DashboardConfig:
    agent_api_base: str
    go_api_base: str
    disable_presentation_mode: bool
    disable_auto_refresh: bool


def load_config() -> DashboardConfig:
    return DashboardConfig(
        agent_api_base=os.getenv("AGENT_API_BASE_URL", "http://localhost:8001").rstrip(
            "/"
        ),
        go_api_base=os.getenv("GO_API_BASE_URL", "http://localhost:8080").rstrip("/"),
        disable_presentation_mode=_env_bool("DISABLE_PRESENTATION_MODE"),
        disable_auto_refresh=_env_bool("DISABLE_AUTO_REFRESH"),
    )
