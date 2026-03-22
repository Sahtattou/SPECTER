from __future__ import annotations

from datetime import datetime
import html
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
    return _json_dict_or_error(response)


def _post_json(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(f"{AGENT_API_BASE}{path}", json=payload or {}, timeout=10)
    response.raise_for_status()
    return _json_dict_or_error(response)


def _get_go_json(path: str) -> Dict[str, Any]:
    response = requests.get(f"{GO_API_BASE}{path}", timeout=10)
    response.raise_for_status()
    return _json_dict_or_error(response)


def _post_go_json(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(f"{GO_API_BASE}{path}", json=payload or {}, timeout=20)
    response.raise_for_status()
    return _json_dict_or_error(response)


def _json_dict_or_error(response: requests.Response) -> Dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise requests.RequestException(
            f"Invalid JSON payload from {response.url}"
        ) from exc
    if isinstance(payload, dict):
        return payload
    raise requests.RequestException(
        f"Unexpected payload type from {response.url}: {type(payload).__name__}"
    )


def _series_from_df(df: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in df.columns:
        return None
    raw = df[column]
    if isinstance(raw, pd.Series):
        return raw
    return None


def _safe_numeric(series: pd.Series | None, default: float = 0.0) -> pd.Series:
    if series is None or series.empty:
        return pd.Series(dtype="float64")
    numeric = pd.to_numeric(series, errors="coerce")
    if isinstance(numeric, pd.Series):
        return numeric.fillna(default)
    return pd.Series(numeric, index=series.index).fillna(default)


def _ensure_bool_mask(mask: Any, index: pd.Index) -> pd.Series:
    if isinstance(mask, pd.Series):
        return mask.fillna(False).astype(bool)
    return pd.Series([False] * len(index), index=index, dtype="bool")


def _filter_with_mask(df: pd.DataFrame, mask: Any) -> pd.DataFrame:
    bool_mask = _ensure_bool_mask(mask, df.index)
    filtered = df.loc[bool_mask]
    if isinstance(filtered, pd.DataFrame):
        return filtered
    return pd.DataFrame(filtered)


def _compute_event_kpis(events: pd.DataFrame) -> Dict[str, Any]:
    if events.empty:
        return {
            "total": 0,
            "unique_sources": 0,
            "poison_detected": 0,
            "poison_detect_rate": 0.0,
            "critical_score": 0,
            "high_score": 0,
            "avg_score": 0.0,
        }

    scores = _safe_numeric(_series_from_df(events, "composite_score"), default=0.0)
    poison = _safe_numeric(_series_from_df(events, "poison_detected"), default=0.0)
    sources = _series_from_df(events, "source_name")
    unique_sources = (
        int(sources.fillna("unknown").nunique()) if sources is not None else 0
    )

    return {
        "total": int(len(events.index)),
        "unique_sources": unique_sources,
        "poison_detected": int((poison == 1).sum()),
        "poison_detect_rate": float(((poison == 1).mean() * 100) if len(poison) else 0.0),
        "critical_score": int((scores >= 85).sum()),
        "high_score": int(((scores >= 70) & (scores < 85)).sum()),
        "avg_score": float(scores.mean()) if len(scores) else 0.0,
    }


def _fmt_time(value: Any) -> str:
    if not value:
        return "unknown"
    text = str(value)
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return text


def _detected_status(value: Any) -> str:
    return "CAUGHT" if value == 1 else ("MISSED" if value == 0 else "PENDING")


st.set_page_config(page_title="SPECTER", layout="wide")

if "refresh_error_count" not in st.session_state:
    st.session_state["refresh_error_count"] = 0
if "last_refresh_success_at" not in st.session_state:
    st.session_state["last_refresh_success_at"] = "never"
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "analysis_error" not in st.session_state:
    st.session_state["analysis_error"] = ""
if "last_action_message" not in st.session_state:
    st.session_state["last_action_message"] = ""
if "artifact_history" not in st.session_state:
    st.session_state["artifact_history"] = []

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

if st.sidebar.button("Retry now", use_container_width=True):
    st.rerun()

event_limit = st.sidebar.slider("Fetch event limit", min_value=25, max_value=500, value=200, step=25)
injection_limit = st.sidebar.slider(
    "Fetch injection limit", min_value=10, max_value=200, value=60, step=10
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;600&display=swap');
    :root {
      --bg: #060913;
      --card: rgba(9, 16, 31, 0.78);
      --card-soft: rgba(13, 23, 46, 0.76);
      --line: rgba(153, 187, 255, 0.24);
      --text: #eaf2ff;
      --muted: #a9c4e6;
      --ok: #39f0b2;
      --warn: #ffd369;
      --bad: #ff6f83;
    }
    .stApp {
      background:
        radial-gradient(1000px 500px at 0% 0%, rgba(0, 215, 255, 0.10), transparent 50%),
        radial-gradient(900px 500px at 100% 0%, rgba(121, 84, 255, 0.12), transparent 52%),
        radial-gradient(1200px 800px at 50% 120%, rgba(57, 240, 178, 0.08), transparent 46%),
        var(--bg);
      color: var(--text);
      font-family: 'Manrope', sans-serif;
    }
    .hero {
      padding: 1.35rem 1.45rem;
      border-radius: 18px;
      background: linear-gradient(130deg, rgba(34, 192, 255, 0.22), rgba(126, 79, 255, 0.22));
      border: 1px solid rgba(181, 208, 255, 0.26);
      box-shadow: 0 18px 45px rgba(5, 10, 20, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }
    .hero h1 {
      margin: 0;
      letter-spacing: -0.02em;
      font-size: 2.05rem;
      color: var(--text);
    }
    .hero p {
      margin: .42rem 0 0 0;
      color: var(--muted);
      max-width: 64rem;
    }
    .hero-badge {
      margin-top: .8rem;
      display: inline-block;
      padding: .2rem .55rem;
      border: 1px solid rgba(211, 232, 255, 0.30);
      background: rgba(7, 14, 28, 0.55);
      color: #d7e9ff;
      border-radius: 999px;
      font-size: .76rem;
      font-family: 'IBM Plex Mono', monospace;
      letter-spacing: .02em;
    }
    .panel {
      padding: .88rem 1rem;
      border-radius: 14px;
      background: var(--card);
      border: 1px solid var(--line);
      backdrop-filter: blur(4px);
    }
    .action-note {
      margin-top: .55rem;
      padding: .45rem .6rem;
      border-radius: 10px;
      background: rgba(27, 43, 72, 0.62);
      border: 1px solid rgba(173, 199, 243, 0.20);
      color: #d4e5ff;
      font-size: .86rem;
    }
    .mini-label {
      color: #9ab5d9;
      font-size: .8rem;
      margin-bottom: .15rem;
      font-family: 'IBM Plex Mono', monospace;
    }
    .caught {color:var(--ok); font-weight:700;}
    .missed {color:var(--bad); font-weight:700;}
    .pending {color:var(--warn); font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>SPECTER — Adversarial Mirror Command Deck</h1>
      <p>Operational dashboard for live red-vs-blue integrity testing: monitor pipeline health, triage high-risk indicators, trigger adversarial scenarios, and export forensic artifacts.</p>
      <span class="hero-badge">THREAT INTEL · LIVE OPS VIEW</span>
    </div>
    """,
    unsafe_allow_html=True,
)

health_left, health_mid, health_right, health_fourth = st.columns([1, 1, 1, 1])

agents_health = "unknown"
go_health = "unknown"

with health_left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='mini-label'>SERVICE STATUS</div>", unsafe_allow_html=True)
    try:
        agents_health_payload = _get_json("/health")
        agents_health = agents_health_payload.get("status", "unknown")
        st.success(f"Agents API: {agents_health}")
    except requests.RequestException as exc:
        st.error(f"Agents API unavailable: {exc}")
        st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

with health_mid:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='mini-label'>SERVICE STATUS</div>", unsafe_allow_html=True)
    try:
        go_health_payload = _get_go_json("/health")
        go_health = go_health_payload.get("status", "unknown")
        st.success(f"Go API: {go_health}")
    except requests.RequestException as exc:
        st.error(f"Go API unavailable: {exc}")
        st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

with health_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='mini-label'>MODE</div>", unsafe_allow_html=True)
    st.info("Presentation" if presentation_mode else "Operations")
    st.markdown("</div>", unsafe_allow_html=True)

with health_fourth:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='mini-label'>ACTIONS</div>", unsafe_allow_html=True)
    st.info("Live enabled" if allow_live_actions else "Read-only")
    st.markdown("</div>", unsafe_allow_html=True)

top_left, top_mid, top_right = st.columns([1.2, 1.2, 2.4])

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
            st.session_state["last_action_message"] = (
                f"Injection sent ({injected.get('attack_type')}) at {time.strftime('%H:%M:%S UTC', time.gmtime())}"
            )
            st.session_state["last_refresh_success_at"] = time.strftime(
                "%H:%M:%S UTC", time.gmtime()
            )
            st.session_state["refresh_error_count"] = 0
        except requests.RequestException as exc:
            st.error(f"Injection trigger failed: {exc}")
            st.session_state["refresh_error_count"] += 1

    scenario_runs = st.slider(
        "Scenario burst size", min_value=1, max_value=10, value=3, step=1
    )
    if st.button(
        "🧪 Run attack burst",
        use_container_width=True,
        disabled=not allow_live_actions,
        help="Triggers multiple injections in sequence for stress testing.",
    ):
        successful_runs = 0
        failed_runs = 0
        for _ in range(scenario_runs):
            try:
                _post_json("/mirror/injections/trigger", trigger_payload)
                successful_runs += 1
            except requests.RequestException:
                failed_runs += 1
        st.session_state["last_action_message"] = (
            f"Burst complete: {successful_runs} success / {failed_runs} failed"
        )
        if failed_runs == 0:
            st.success(st.session_state["last_action_message"])
            st.session_state["refresh_error_count"] = 0
        else:
            st.warning(st.session_state["last_action_message"])
            st.session_state["refresh_error_count"] += failed_runs
    st.markdown("</div>", unsafe_allow_html=True)

with top_mid:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Export Actions")
    if st.button(
        "📦 Export STIX", use_container_width=True, disabled=not allow_live_actions
    ):
        try:
            stix = _post_go_json("/api/v1/exports/stix")
            stix_path = str(stix.get("artifact_path", "(path unavailable)"))
            st.success(f"STIX ready: {stix.get('artifact_path', '(path unavailable)')}")
            st.session_state["last_action_message"] = "STIX export completed successfully"
            st.session_state["artifact_history"] = [
                {
                    "kind": "STIX",
                    "path": stix_path,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                },
                *st.session_state["artifact_history"],
            ][:8]
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
            report_path = str(report.get("artifact_path", "(path unavailable)"))
            st.success(
                f"Report ready: {report.get('artifact_path', '(path unavailable)')}"
            )
            st.session_state["last_action_message"] = "Report export completed successfully"
            st.session_state["artifact_history"] = [
                {
                    "kind": "REPORT",
                    "path": report_path,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                },
                *st.session_state["artifact_history"],
            ][:8]
            st.session_state["last_refresh_success_at"] = time.strftime(
                "%H:%M:%S UTC", time.gmtime()
            )
            st.session_state["refresh_error_count"] = 0
        except requests.RequestException as exc:
            st.error(f"Report export failed: {exc}")
            st.session_state["refresh_error_count"] += 1

    with st.expander("Blue analyst summary", expanded=False):
        analysis_limit = st.slider(
            "Blue analysis window", min_value=25, max_value=500, value=120, step=25
        )
        if st.button(
            "🧠 Run Blue Analyst",
            use_container_width=True,
            disabled=not allow_live_actions,
            help="Calls the blue analyst chain for recommendations and top IOC focus list.",
        ):
            try:
                analysis = _post_json("/agents/blue/analyze", {"limit": analysis_limit})
                st.session_state["analysis_result"] = analysis
                st.session_state["analysis_error"] = ""
                st.session_state["last_action_message"] = "Blue analyst run completed"
                st.success("Blue analyst completed")
            except requests.RequestException as exc:
                st.session_state["analysis_result"] = None
                st.session_state["analysis_error"] = str(exc)
                st.error(f"Blue analyst failed: {exc}")

        if st.session_state["analysis_error"]:
            st.warning(st.session_state["analysis_error"])

        if isinstance(st.session_state["analysis_result"], dict):
            result = st.session_state["analysis_result"]
            st.markdown(f"**Summary:** {result.get('summary', 'No summary available')} ")
            recs = result.get("recommended_actions", [])
            if recs:
                st.markdown("**Recommended actions**")
                for action in recs:
                    st.write(f"- {action}")
            top_iocs = result.get("top_iocs", [])
            if top_iocs:
                st.markdown("**Top IOCs**")
                st.code("\n".join(top_iocs), language="text")

    if st.session_state["artifact_history"]:
        with st.expander("Recent artifacts", expanded=False):
            for artifact in st.session_state["artifact_history"]:
                st.markdown(
                    f"- **{artifact['kind']}** · `{artifact['path']}` · {artifact['created_at']}"
                )
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Pipeline Metrics")
    metrics: Dict[str, Any] = {}
    try:
        metrics = _get_json("/mirror/metrics")
        cols = st.columns(6)
        cols[0].metric("Total Events", metrics.get("total_events", 0))
        cols[1].metric("Validated", metrics.get("validated_events", 0))
        cols[2].metric("Quarantined", metrics.get("quarantined_events", 0))
        cols[3].metric("Injections", metrics.get("total_injections", 0))
        cols[4].metric("Caught", metrics.get("caught_injections", 0))
        cols[5].metric("Catch Rate %", metrics.get("catch_rate_percent", 0.0))

        validate_rate = 0.0
        total_events = float(metrics.get("total_events", 0) or 0)
        validated_events = float(metrics.get("validated_events", 0) or 0)
        if total_events > 0:
            validate_rate = (validated_events / total_events) * 100

        injection_total = float(metrics.get("total_injections", 0) or 0)
        caught_total = float(metrics.get("caught_injections", 0) or 0)
        missed_total = max(injection_total - caught_total, 0)
        resilience_score = (caught_total / injection_total) * 100 if injection_total > 0 else None

        extra = st.columns(4)
        extra[0].metric("Validation Rate %", round(validate_rate, 1))
        extra[1].metric("Missed Injections", int(missed_total))
        resilience_display = "N/A" if resilience_score is None else round(resilience_score, 1)
        extra[2].metric("Resilience Score", resilience_display)
        extra[3].metric("Refresh Errors", st.session_state["refresh_error_count"])

        if resilience_score is None:
            st.info("Resilience score will appear after at least one injection.")
        elif resilience_score < 70:
            st.error("Detection resilience is degraded. Prioritize review of missed injections.")
        elif resilience_score < 90:
            st.warning("Detection is partially effective. Investigate attack profiles causing misses.")
        else:
            st.success("Detection resilience is healthy.")

        st.session_state["last_refresh_success_at"] = time.strftime(
            "%H:%M:%S UTC", time.gmtime()
        )
    except requests.RequestException as exc:
        st.warning(f"Could not load metrics: {exc}")
        st.session_state["refresh_error_count"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state["last_action_message"]:
    action_note = html.escape(str(st.session_state["last_action_message"]))
    st.markdown(
        f"<div class='action-note'>Latest action: {action_note}</div>",
        unsafe_allow_html=True,
    )

if st.session_state["refresh_error_count"] > 0:
    st.warning(
        "One or more upstream calls failed recently. Use Retry now or wait for auto-refresh backoff."
    )

left, right = st.columns([1.25, 1])

with left:
    st.subheader("Live IOC Feed")
    events: List[Dict[str, Any]] = []
    try:
        events_payload = _get_json(f"/mirror/events?limit={event_limit}")
        events = events_payload.get("events", [])
        if events:
            df = pd.DataFrame(events)
            if "composite_score" in df.columns:
                df["composite_score"] = _safe_numeric(
                    _series_from_df(df, "composite_score"), default=0.0
                )
            if "corroboration_count" in df.columns:
                df["corroboration_count"] = _safe_numeric(
                    _series_from_df(df, "corroboration_count"), default=0.0
                )
            if "domain_age_days" in df.columns:
                df["domain_age_days"] = _safe_numeric(
                    _series_from_df(df, "domain_age_days"), default=0.0
                )

            filters_col1, filters_col2, filters_col3, filters_col4 = st.columns([1, 1, 1, 1.2])

            with filters_col1:
                stage_values = sorted(df["pipeline_stage"].dropna().unique().tolist()) if "pipeline_stage" in df.columns else []
                selected_stages = st.multiselect(
                    "Stage filter", options=stage_values, default=stage_values
                )

            with filters_col2:
                ioc_types = sorted(df["ioc_type"].dropna().unique().tolist()) if "ioc_type" in df.columns else []
                selected_ioc_types = st.multiselect(
                    "IOC type filter", options=ioc_types, default=ioc_types
                )

            with filters_col3:
                sources = sorted(df["source_name"].dropna().unique().tolist()) if "source_name" in df.columns else []
                selected_sources = st.multiselect(
                    "Source filter", options=sources, default=sources
                )

            with filters_col4:
                min_score = st.slider(
                    "Minimum score",
                    min_value=0,
                    max_value=100,
                    value=0,
                    step=5,
                    help="Show only events with composite score >= threshold.",
                )

            search_text = st.text_input(
                "Search IOC value", value="", placeholder="e.g. suspicious-domain.tld or IP"
            ).strip()

            filtered_df: pd.DataFrame = df.copy()
            if "pipeline_stage" in filtered_df.columns:
                stage_series = _series_from_df(filtered_df, "pipeline_stage")
                if stage_series is not None:
                    filtered_df = _filter_with_mask(
                        filtered_df, stage_series.isin(selected_stages)
                    )
            if "ioc_type" in filtered_df.columns:
                ioc_series = _series_from_df(filtered_df, "ioc_type")
                if ioc_series is not None:
                    filtered_df = _filter_with_mask(
                        filtered_df, ioc_series.isin(selected_ioc_types)
                    )
            if "source_name" in filtered_df.columns:
                source_series = _series_from_df(filtered_df, "source_name")
                if source_series is not None:
                    filtered_df = _filter_with_mask(
                        filtered_df, source_series.isin(selected_sources)
                    )
            if "composite_score" in filtered_df.columns:
                score_mask = filtered_df["composite_score"] >= min_score
                filtered_df = _filter_with_mask(filtered_df, score_mask)
            if search_text and "raw_value" in filtered_df.columns:
                raw_value_series = _series_from_df(filtered_df, "raw_value")
                if raw_value_series is not None:
                    text_mask = raw_value_series.astype(str).str.contains(
                        search_text,
                        case=False,
                        regex=False,
                        na=False,
                    )
                    filtered_df = _filter_with_mask(filtered_df, text_mask)

            sort_columns = []
            if "composite_score" in filtered_df.columns:
                sort_columns.append("composite_score")
            if "collected_at" in filtered_df.columns:
                sort_columns.append("collected_at")
            if sort_columns:
                filtered_df = filtered_df.sort_values(
                    by=sort_columns,
                    ascending=[False] * len(sort_columns),
                )

            kpis = _compute_event_kpis(filtered_df)
            kpi_cols = st.columns(7)
            kpi_cols[0].metric("Filtered Events", kpis["total"])
            kpi_cols[1].metric("Unique Sources", kpis["unique_sources"])
            kpi_cols[2].metric("Poison Detected", kpis["poison_detected"])
            kpi_cols[3].metric("Poison Detect %", round(kpis["poison_detect_rate"], 1))
            kpi_cols[4].metric("Critical (≥85)", kpis["critical_score"])
            kpi_cols[5].metric("High (70-84)", kpis["high_score"])
            kpi_cols[6].metric("Avg Score", round(kpis["avg_score"], 1))

            preferred = [
                "collected_at",
                "ioc_type",
                "raw_value",
                "source_name",
                "pipeline_stage",
                "corroboration_count",
                "domain_age_days",
                "poison_detected",
                "detection_rule",
                "composite_score",
            ]
            visible_cols = [col for col in preferred if col in filtered_df.columns]

            if not filtered_df.empty:
                if "collected_at" in filtered_df.columns:
                    filtered_df["collected_at"] = filtered_df["collected_at"].apply(_fmt_time)

                st.dataframe(
                    filtered_df[visible_cols], use_container_width=True, hide_index=True
                )

                csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download filtered events CSV",
                    data=csv_bytes,
                    file_name="specter_filtered_events.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning("No events match current filters. Broaden filters to continue triage.")

            stage_counts = (
                filtered_df["pipeline_stage"]
                .value_counts()
                .rename_axis("stage")
                .reset_index(name="count")
                if "pipeline_stage" in filtered_df.columns and not filtered_df.empty
                else pd.DataFrame()
            )

            source_counts = (
                filtered_df["source_name"]
                .fillna("unknown")
                .value_counts()
                .head(8)
                .rename_axis("source")
                .reset_index(name="count")
                if "source_name" in filtered_df.columns and not filtered_df.empty
                else pd.DataFrame()
            )

            chart_left, chart_right = st.columns(2)
            if not stage_counts.empty:
                with chart_left:
                    st.caption("Pipeline stage distribution")
                    st.bar_chart(stage_counts.set_index("stage"))
            if not source_counts.empty:
                with chart_right:
                    st.caption("Top source distribution")
                    st.bar_chart(source_counts.set_index("source"))

            if "composite_score" in filtered_df.columns and not filtered_df.empty:
                st.caption("Score trend (descending by risk)")
                trend_df = (
                    filtered_df[["composite_score"]]
                    .reset_index(drop=True)
                    .rename({"composite_score": "score"}, axis=1)
                )
                st.line_chart(trend_df)
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
        inj_payload = _get_json(f"/mirror/injections?limit={injection_limit}")
        injections: List[Dict[str, Any]] = inj_payload.get("injections", [])
        if not injections:
            st.info("No injections logged yet.")
        else:
            inj_df = pd.DataFrame(injections)
            if "attack_type" in inj_df.columns:
                attack_types = sorted(inj_df["attack_type"].dropna().unique().tolist())
            else:
                attack_types = []
            selected_attacks = st.multiselect(
                "Attack type filter", options=attack_types, default=attack_types
            )
            detection_filter = st.selectbox(
                "Detection status",
                ["ALL", "CAUGHT", "MISSED", "PENDING"],
                index=0,
            )

            if "attack_type" in inj_df.columns:
                attack_series = _series_from_df(inj_df, "attack_type")
                if attack_series is not None:
                    inj_df = _filter_with_mask(inj_df, attack_series.isin(selected_attacks))

            if "detected" in inj_df.columns and detection_filter != "ALL":
                target_status = {"CAUGHT": 1, "MISSED": 0, "PENDING": -1}[detection_filter]
                if target_status == -1:
                    detected_col = _series_from_df(inj_df, "detected")
                    if detected_col is not None:
                        inj_df = _filter_with_mask(inj_df, detected_col.isna())
                else:
                    detected_series = _safe_numeric(
                        _series_from_df(inj_df, "detected"), default=-1
                    )
                    inj_df = _filter_with_mask(inj_df, detected_series == target_status)

            caught_count = 0
            missed_count = 0
            pending_count = 0

            if "detected" in inj_df.columns:
                status_series = _safe_numeric(_series_from_df(inj_df, "detected"), default=-1)
                caught_count = int((status_series == 1).sum())
                missed_count = int((status_series == 0).sum())
                pending_count = int((status_series < 0).sum())

            stat_cols = st.columns(3)
            stat_cols[0].metric("Caught", caught_count)
            stat_cols[1].metric("Missed", missed_count)
            stat_cols[2].metric("Pending", pending_count)

            if inj_df.empty:
                st.warning("No injection records match current filters.")

            for item in inj_df.to_dict("records"):
                status = _detected_status(item.get("detected"))
                status_class = (
                    "caught"
                    if status == "CAUGHT"
                    else ("missed" if status == "MISSED" else "pending")
                )
                attack_label = html.escape(str(item.get("attack_type", "unknown")))
                raw_value = html.escape(str(item.get("raw_value", "unknown")))
                injected_label = html.escape(_fmt_time(item.get("injected_at")))
                st.markdown(
                    f"""
                    <div class='panel' style='margin-bottom:.55rem;'>
                      <div><strong>{attack_label}</strong> · {raw_value}</div>
                      <div style='font-size:.86rem; color:#9bb2d7;'>{injected_label}</div>
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
