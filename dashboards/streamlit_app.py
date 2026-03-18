from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

st = __import__("streamlit")

AGENT_API_BASE = os.getenv("AGENT_API_BASE_URL", "http://localhost:8001").rstrip("/")


def _get_json(path: str) -> Dict[str, Any]:
    response = requests.get(f"{AGENT_API_BASE}{path}", timeout=10)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return payload
    return {}


def _post_json(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(f"{AGENT_API_BASE}{path}", json=payload or {}, timeout=10)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict):
        return result
    return {}


st.set_page_config(page_title="SPECTER", layout="wide")
st.title("SPECTER Adversarial Mirror Dashboard")

if st.button("Trigger injection now", type="primary"):
    try:
        injected = _post_json("/mirror/injections/trigger")
        st.success(
            f"Injection submitted: {injected.get('attack_type')} · {injected.get('raw_value')}"
        )
    except requests.RequestException as exc:
        st.error(f"Injection trigger failed: {exc}")

left, right = st.columns(2)

with left:
    st.subheader("Live IOC Feed")
    try:
        events_payload = _get_json("/mirror/events?limit=50")
        events: List[Dict[str, Any]] = events_payload.get("events", [])
        st.dataframe(events, use_container_width=True, hide_index=True)
    except requests.RequestException as exc:
        st.warning(f"Could not load events: {exc}")

with right:
    st.subheader("Red Agent Activity")
    try:
        inj_payload = _get_json("/mirror/injections?limit=50")
        injections: List[Dict[str, Any]] = inj_payload.get("injections", [])
        for item in injections:
            detected = item.get("detected")
            status = (
                "CAUGHT"
                if detected == 1
                else ("MISSED" if detected == 0 else "PENDING")
            )
            st.write(
                f"{item.get('injected_at')} · {item.get('attack_type')} · {item.get('raw_value')} · {status}"
            )
    except requests.RequestException as exc:
        st.warning(f"Could not load injections: {exc}")

st.subheader("Pipeline Metrics")
try:
    metrics = _get_json("/mirror/metrics")
    cols = st.columns(6)
    cols[0].metric("Total Events", metrics.get("total_events", 0))
    cols[1].metric("Validated", metrics.get("validated_events", 0))
    cols[2].metric("Quarantined", metrics.get("quarantined_events", 0))
    cols[3].metric("Injections", metrics.get("total_injections", 0))
    cols[4].metric("Caught", metrics.get("caught_injections", 0))
    cols[5].metric("Catch Rate %", metrics.get("catch_rate_percent", 0.0))
except requests.RequestException as exc:
    st.warning(f"Could not load metrics: {exc}")
