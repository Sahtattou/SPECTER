from __future__ import annotations

from typing import Any, Dict

from app.chains.blue_analyst_chain import run_blue_analyst_chain
from app.chains.red_injector_chain import run_red_injector_chain
from app.clients.go_api_client import GoAPIClient


def _dump_model(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError("unsupported response object")


def run_agent(
    name: str,
    client: GoAPIClient,
    *,
    limit: int = 100,
    dry_run: bool = True,
) -> Dict[str, Any]:
    if name == "blue_analyst":
        return _dump_model(run_blue_analyst_chain(client=client, limit=limit))
    if name == "red_injector":
        return _dump_model(run_red_injector_chain(client=client, dry_run=dry_run))
    raise ValueError(f"unsupported agent '{name}'")
