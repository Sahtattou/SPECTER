from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


class GoAPIClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10, max_retries: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._session = requests.Session()

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        last_error: Optional[Exception] = None

        for _ in range(self.max_retries + 1):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                if not response.text.strip():
                    return {}
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise RuntimeError("request failed without an explicit error")

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def get_recent_events(self, limit: int = 100, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/api/v1/events?limit={limit}"
        if stage:
            path += f"&stage={stage}"

        result = self._request("GET", path)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            events = result.get("events", [])
            if isinstance(events, list):
                return events
        return []

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        result = self._request("GET", "/api/v1/metrics/pipeline")
        return result if isinstance(result, dict) else {}

    def submit_synthetic_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self._request("POST", "/api/v1/agents/injections/trigger", payload)
        return result if isinstance(result, dict) else {}
