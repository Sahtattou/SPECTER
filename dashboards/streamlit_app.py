from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import requests
import pandas as pd

st = __import__("streamlit")

AGENT_API_BASE = os.getenv("AGENT_API_BASE_URL", "http://localhost:8001").rstrip("/")
GO_API_BASE = os.getenv("GO_API_BASE_URL", "http://localhost:8080").rstrip("/")
DISABLE_PRESENTATION_MODE = os.getenv("DISABLE_PRESENTATION_MODE", "false").lower() in {
    "1",
    "true",
    "yes",
}
DISABLE_AUTO_REFRESH = os.getenv("DISABLE_AUTO_REFRESH", "false").lower() in {
    "1",
    "true",
    "yes",
}


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


def _post_go_json(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(f"{GO_API_BASE}{path}", json=payload or {}, timeout=20)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict):
        return result
    return {}


def _detected_status(value: Any) -> str:
    return "CAUGHT" if value == 1 else ("MISSED" if value == 0 else "PENDING")


def _origin_label(event: Dict[str, Any]) -> str:
    return (
        "Injected simulation" if bool(event.get("is_synthetic")) else "Real telemetry"
    )


def _verdict_label(event: Dict[str, Any]) -> str:
    stage = str(event.get("pipeline_stage") or "")
    poison_detected = event.get("poison_detected")
    is_synthetic = bool(event.get("is_synthetic"))
    if stage == "quarantined" and poison_detected is True:
        return "Detected (Quarantined)"
    if stage in {"validated", "scored"} and poison_detected is False:
        return "Passed Validation"
    if is_synthetic and poison_detected is False:
        return "Missed Injection"
    return "Needs Review"


st.set_page_config(page_title="SPECTER", layout="wide")

if "refresh_error_count" not in st.session_state:
    st.session_state["refresh_error_count"] = 0
if "last_refresh_success_at" not in st.session_state:
    st.session_state["last_refresh_success_at"] = "never"

st.sidebar.header("Operator Controls")
presentation_mode = False
if DISABLE_PRESENTATION_MODE:
    st.sidebar.info("Presentation mode disabled by environment kill switch.")
else:
    presentation_mode = st.sidebar.toggle("Presentation mode", value=False)

allow_live_actions = st.sidebar.checkbox(
    "Allow live actions",
    value=not presentation_mode,
    help="Disable to run read-only presentation mode.",
)

if DISABLE_AUTO_REFRESH:
    st.sidebar.info("Auto-refresh disabled by environment kill switch.")
    auto_refresh_seconds = 0
else:
    auto_refresh_seconds = st.sidebar.selectbox(
        "Auto-refresh", [0, 5, 10, 15, 30], index=0
    )

st.sidebar.caption(
    f"Last successful refresh: {st.session_state['last_refresh_success_at']}"
)
st.sidebar.caption(f"Refresh error count: {st.session_state['refresh_error_count']}")

st.markdown(
    """
    <style>
    .stApp {background: radial-gradient(1200px 700px at 15% 10%, #101a2f 0%, #090d18 45%, #05070d 100%);} 
    .hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(135deg, rgba(0,180,255,0.18), rgba(110,65,255,0.16)); border: 1px solid rgba(140,180,255,0.25);} 
    .hero h1 {margin: 0; font-size: 2rem; color: #e9f3ff;}
    .hero p {margin: .35rem 0 0 0; color: #a9c4e6;}
    .panel {padding: .8rem 1rem; border-radius: 14px; background: rgba(9,16,31,0.72); border: 1px solid rgba(124,151,193,0.25);} 
    .caught {color:#42f5b0; font-weight:700;}
    .missed {color:#ff6d7a; font-weight:700;}
    .pending {color:#ffcf66; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='panel' style='margin-top:.75rem;'>
      <strong>Adversarial mirror dynamics (same semantics as PDF)</strong><br/>
      BLUE = Real telemetry ingestion · RED = Injected simulation challenge · DETECTOR = Verdict assignment.<br/>
      Labels are text-first: <em>Real telemetry</em>, <em>Injected simulation</em>, <em>Detected (Quarantined)</em>, <em>Passed Validation</em>, <em>Missed Injection</em>, <em>Needs Review</em>.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>SPECTER — Adversarial Mirror Command Deck</h1>
      <p>Live blue-vs-red validation feed for jury demo: inject, detect, validate, and export in real time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_mid, top_right = st.columns([1.2, 1.2, 2])

with top_left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Red Agent Controls")
    attack = st.selectbox(
        "Attack profile",
        [
            "AUTO",
            "REPUTATION_LAUNDERING",
            "GHOST_DOMAIN",
            "TTP_MISMATCH",
            "TIMESTAMP_MANIPULATION",
        ],
        index=0,
    )
    trigger_payload = None if attack == "AUTO" else {"attack_type": attack}
    if st.button(
        "⚡ Trigger injection now",
        type="primary",
        use_container_width=True,
        disabled=not allow_live_actions,
    ):
        try:
            injected = _post_json("/mirror/injections/trigger", trigger_payload)
            st.success(
                f"Injected: {injected.get('attack_type')} · {injected.get('raw_value')}"
            )
            st.session_state["last_refresh_success_at"] = time.strftime(
                "%H:%M:%S UTC", time.gmtime()
            )
            st.session_state["refresh_error_count"] = 0
        except requests.RequestException as exc:
            st.error(f"Injection trigger failed: {exc}")
            st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

with top_mid:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Export Actions")
    if st.button(
        "📦 Export STIX", use_container_width=True, disabled=not allow_live_actions
    ):
        try:
            stix = _post_go_json("/api/v1/exports/stix")
            st.success(f"STIX ready: {stix.get('artifact_path', '(path unavailable)')}")
            st.session_state["last_refresh_success_at"] = time.strftime(
                "%H:%M:%S UTC", time.gmtime()
            )
            st.session_state["refresh_error_count"] = 0
        except requests.RequestException as exc:
            st.error(f"STIX export failed: {exc}")
            st.session_state["refresh_error_count"] += 1

    if st.button(
        "🧾 Export Report", use_container_width=True, disabled=not allow_live_actions
    ):
        try:
            report = _post_go_json("/api/v1/exports/report")
            st.success(
                f"Report ready: {report.get('artifact_path', '(path unavailable)')}"
            )
            st.session_state["last_refresh_success_at"] = time.strftime(
                "%H:%M:%S UTC", time.gmtime()
            )
            st.session_state["refresh_error_count"] = 0
        except requests.RequestException as exc:
            st.error(f"Report export failed: {exc}")
            st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
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

        dyn = st.columns(4)
        total_events = int(metrics.get("total_events", 0))
        total_injections = int(metrics.get("total_injections", 0))
        caught = int(metrics.get("caught_injections", 0))
        dyn[0].metric("BLUE Real", max(total_events - total_injections, 0))
        dyn[1].metric("RED Injected", total_injections)
        dyn[2].metric("DETECTOR Caught", caught)
        dyn[3].metric("DETECTOR Missed", max(total_injections - caught, 0))

        balance = st.columns(4)
        balance[0].metric("Red/Blue Ratio", metrics.get("red_blue_ratio", 0.0))
        balance[1].metric("Ratio Limit", metrics.get("red_max_ratio", 1.0))
        balance[2].metric(
            "Min Real Before Auto-Red",
            metrics.get("min_real_events_before_auto_red", 0),
        )
        gate_allowed = metrics.get("auto_red_last_allowed")
        gate_label = (
            "ALLOWED"
            if gate_allowed is True
            else ("THROTTLED" if gate_allowed is False else "UNKNOWN")
        )
        balance[3].metric("Auto-Red Gate", gate_label)
        st.caption(
            f"Auto-red reason: {metrics.get('auto_red_last_reason', 'n/a')} · Last evaluated ratio: {metrics.get('auto_red_last_ratio', 0.0)}"
        )
        st.session_state["last_refresh_success_at"] = time.strftime(
            "%H:%M:%S UTC", time.gmtime()
        )
        st.session_state["refresh_error_count"] = 0
    except requests.RequestException as exc:
        st.warning(f"Could not load metrics: {exc}")
        st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns([1.25, 1])

with left:
    st.subheader("Live IOC Feed")
    try:
        events_payload = _get_json("/mirror/events?limit=50")
        events: List[Dict[str, Any]] = events_payload.get("events", [])
        if events:
            for event in events:
                event["origin"] = _origin_label(event)
                event["detector_verdict"] = _verdict_label(event)

            df = pd.DataFrame(events)
            preferred = [
                "collected_at",
                "origin",
                "ioc_type",
                "raw_value",
                "source_name",
                "pipeline_stage",
                "detector_verdict",
                "corroboration_count",
                "domain_age_days",
                "poison_detected",
                "detection_rule",
                "composite_score",
            ]
            visible_cols = [col for col in preferred if col in df.columns]
            st.dataframe(df[visible_cols], use_container_width=True, hide_index=True)

            flow_cols = st.columns(3)
            blue_df = df[df["origin"] == "Real telemetry"]
            red_df = df[df["origin"] == "Injected simulation"]
            verdict_counts = (
                df["detector_verdict"]
                .value_counts()
                .rename_axis("verdict")
                .reset_index(name="count")
            )

            with flow_cols[0]:
                st.caption("BLUE Agent stream")
                st.metric("Real telemetry records", int(len(blue_df)))
            with flow_cols[1]:
                st.caption("RED Agent stream")
                st.metric("Injected simulation records", int(len(red_df)))
            with flow_cols[2]:
                st.caption("DETECTOR verdict states")
                st.metric("Distinct verdict labels", int(len(verdict_counts)))

            if not verdict_counts.empty:
                st.caption("Detector verdict distribution")
                st.bar_chart(verdict_counts.set_index("verdict"))

            if not blue_df.empty:
                st.caption("Top BLUE highlights (real telemetry)")
                blue_cols = [
                    c
                    for c in [
                        "collected_at",
                        "raw_value",
                        "pipeline_stage",
                        "detector_verdict",
                        "composite_score",
                    ]
                    if c in blue_df.columns
                ]
                blue_subset = pd.DataFrame(blue_df[blue_cols])
                st.dataframe(
                    blue_subset.head(8),
                    use_container_width=True,
                    hide_index=True,
                )

            if not red_df.empty:
                st.caption("Top RED highlights (injected simulation)")
                red_cols = [
                    c
                    for c in [
                        "collected_at",
                        "raw_value",
                        "pipeline_stage",
                        "detector_verdict",
                        "detection_rule",
                        "composite_score",
                    ]
                    if c in red_df.columns
                ]
                red_subset = pd.DataFrame(red_df[red_cols])
                st.dataframe(
                    red_subset.head(8), use_container_width=True, hide_index=True
                )

            stage_counts = (
                df["pipeline_stage"]
                .value_counts()
                .rename_axis("stage")
                .reset_index(name="count")
                if "pipeline_stage" in df.columns
                else pd.DataFrame()
            )
            if not stage_counts.empty:
                st.caption("Pipeline stage distribution")
                st.bar_chart(stage_counts.set_index("stage"))
        else:
            st.info(
                "No events yet. Trigger an injection or ingest data to populate the feed."
            )
    except requests.RequestException as exc:
        st.warning(f"Could not load events: {exc}")
        st.session_state["refresh_error_count"] += 1

with right:
    st.subheader("Red Agent Activity")
    try:
        inj_payload = _get_json("/mirror/injections?limit=50")
        injections: List[Dict[str, Any]] = inj_payload.get("injections", [])
        if not injections:
            st.info("No injections logged yet.")
        else:
            for item in injections:
                status = _detected_status(item.get("detected"))
                status_class = (
                    "caught"
                    if status == "CAUGHT"
                    else ("missed" if status == "MISSED" else "pending")
                )
                st.markdown(
                    f"""
                    <div class='panel' style='margin-bottom:.55rem;'>
                      <div><strong>{item.get("attack_type")}</strong> · {item.get("raw_value")}</div>
                      <div style='font-size:.86rem; color:#9bb2d7;'>{item.get("injected_at")}</div>
                      <div style='font-size:.8rem; color:#c5d7ee;'>Origin: Injected simulation (RED)</div>
                      <div class='{status_class}'>{status}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except requests.RequestException as exc:
        st.warning(f"Could not load injections: {exc}")
        st.session_state["refresh_error_count"] += 1

if auto_refresh_seconds > 0 and not DISABLE_AUTO_REFRESH:
    penalty_multiplier = 2 ** min(st.session_state["refresh_error_count"], 3)
    next_refresh = min(auto_refresh_seconds * penalty_multiplier, 60)
    st.caption(f"Auto-refresh active: next refresh in ~{next_refresh}s")
    time.sleep(next_refresh)
    st.rerun()
