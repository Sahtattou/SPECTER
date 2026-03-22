from __future__ import annotations

import html
from typing import Any

import pandas as pd
import requests

from .api import get_agent_json, get_go_json, post_agent_json, post_go_json
from .config import DashboardConfig
from .domain import detected_status, origin_label, status_css_class, verdict_label
from .sidebar import SidebarControls
from .state import bump_refresh_errors, mark_refresh_success

st = __import__("streamlit")


def render_control_strip(config: DashboardConfig, controls: SidebarControls) -> None:
    top_left, top_mid, top_right = st.columns([1.2, 1.2, 2])

    with top_left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(
            "<p class='panel-title'>Red Team Controls</p>", unsafe_allow_html=True
        )
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
            "⚡ Launch injection",
            type="primary",
            use_container_width=True,
            disabled=not controls.allow_live_actions,
        ):
            try:
                injected = post_agent_json(
                    config, "/mirror/injections/trigger", trigger_payload
                )
                st.success(
                    f"Injected: {injected.get('attack_type')} · {injected.get('raw_value')}"
                )
                mark_refresh_success()
            except (requests.RequestException, ValueError) as exc:
                st.error(f"Injection trigger failed: {exc}")
                bump_refresh_errors()
        st.markdown("</div>", unsafe_allow_html=True)

    with top_mid:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(
            "<p class='panel-title'>Artifact Exports</p>", unsafe_allow_html=True
        )
        if st.button(
            "📦 Export STIX",
            use_container_width=True,
            disabled=not controls.allow_live_actions,
        ):
            try:
                stix = post_go_json(config, "/api/v1/exports/stix")
                st.success(
                    f"STIX ready: {stix.get('artifact_path', '(path unavailable)')}"
                )
                mark_refresh_success()
            except (requests.RequestException, ValueError) as exc:
                st.error(f"STIX export failed: {exc}")
                bump_refresh_errors()

        if st.button(
            "🧾 Export Report",
            use_container_width=True,
            disabled=not controls.allow_live_actions,
        ):
            try:
                report = post_go_json(config, "/api/v1/exports/report")
                st.success(
                    f"Report ready: {report.get('artifact_path', '(path unavailable)')}"
                )
                mark_refresh_success()
            except (requests.RequestException, ValueError) as exc:
                st.error(f"Report export failed: {exc}")
                bump_refresh_errors()
        st.markdown("</div>", unsafe_allow_html=True)

    with top_right:
        _render_pipeline_metrics(config)


def _render_pipeline_metrics(config: DashboardConfig) -> None:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<p class='panel-title'>Pipeline Overview</p>", unsafe_allow_html=True)
    mirror_metrics: dict[str, Any] = {}
    go_metrics: dict[str, Any] = {}
    metrics_errors: list[str] = []

    try:
        mirror_metrics = get_agent_json(config, "/mirror/metrics")
    except (requests.RequestException, ValueError) as exc:
        metrics_errors.append(f"Could not load mirror metrics: {exc}")

    try:
        go_metrics = get_go_json(config, "/api/v1/metrics/pipeline")
    except (requests.RequestException, ValueError) as exc:
        metrics_errors.append(f"Could not load Go pipeline metrics: {exc}")

    if not go_metrics and not mirror_metrics:
        st.warning("Could not load any metrics endpoint.")
        bump_refresh_errors()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    row1 = st.columns(4)
    row1[0].metric("Total Events", go_metrics.get("total_events", 0))
    row1[1].metric("Injections", mirror_metrics.get("total_injections", 0))
    row1[2].metric("Caught", mirror_metrics.get("caught_injections", 0))
    row1[3].metric(
        "Catch Rate",
        f"{mirror_metrics.get('catch_rate_percent', 0.0):.1f}%",
    )

    total_events_mirror = int(mirror_metrics.get("total_events", 0))
    total_injections = int(mirror_metrics.get("total_injections", 0))
    caught = int(mirror_metrics.get("caught_injections", 0))
    missed = max(total_injections - caught, 0)
    real_events = int(
        mirror_metrics.get(
            "real_events", max(total_events_mirror - total_injections, 0)
        )
    )

    row2 = st.columns(4)
    row2[0].metric("Real (BLUE)", real_events)
    row2[1].metric("Injected (RED)", total_injections)
    row2[2].metric("Missed", missed)
    ratio = mirror_metrics.get("red_blue_ratio", 0.0)
    gate_allowed = mirror_metrics.get("auto_red_last_allowed")
    gate = (
        "OK"
        if gate_allowed is True
        else ("THROTTLED" if gate_allowed is False else "—")
    )
    row2[3].metric("Red/Blue", f"{ratio:.2f} / {gate}")

    freshness_age = go_metrics.get("freshness_age_seconds")
    freshness_display = (
        f"{int(freshness_age)}s"
        if isinstance(freshness_age, (int, float)) and freshness_age is not None
        else "n/a"
    )
    row3 = st.columns(3)
    row3[0].metric(
        "Last Collected",
        go_metrics.get("last_collected_at", "—")[:19]
        if go_metrics.get("last_collected_at")
        else "—",
    )
    row3[1].metric("Freshness Age", freshness_display)
    row3[2].metric("Sources", go_metrics.get("distinct_sources", 0))

    if metrics_errors:
        bump_refresh_errors()
    else:
        mark_refresh_success()

    for error in metrics_errors:
        st.warning(error)
    st.markdown("</div>", unsafe_allow_html=True)


def render_feed_panels(config: DashboardConfig) -> None:
    left, right = st.columns([1.25, 1])

    with left:
        _render_ioc_feed(config)

    with right:
        _render_red_activity(config)


def _render_ioc_feed(config: DashboardConfig) -> None:
    st.subheader("Live IOC Feed")
    try:
        events_payload = get_agent_json(config, "/mirror/events?limit=50")
        events: list[dict[str, Any]] = events_payload.get("events", [])
        if not events:
            st.info(
                "No events yet. Trigger an injection or ingest data to populate the feed."
            )
            return

        for event in events:
            event["origin"] = origin_label(event)
            event["detector_verdict"] = verdict_label(event)

        df = pd.DataFrame(events)
        preferred = [
            "collected_at",
            "origin",
            "ioc_type",
            "raw_value",
            "detector_verdict",
            "composite_score",
        ]
        visible_cols = [col for col in preferred if col in df.columns]
        st.dataframe(df[visible_cols], use_container_width=True, hide_index=True)

        blue_df = df[df["origin"] == "Real telemetry"]
        red_df = df[df["origin"] == "Injected simulation"]
        verdict_counts = (
            df["detector_verdict"]
            .value_counts()
            .rename_axis("verdict")
            .reset_index(name="count")
        )

        stream_cols = st.columns(3)
        stream_cols[0].metric("Real (BLUE)", int(len(blue_df)))
        stream_cols[1].metric("Injected (RED)", int(len(red_df)))
        stream_cols[2].metric("Verdicts", int(len(verdict_counts)))

        if not verdict_counts.empty:
            st.bar_chart(verdict_counts.set_index("verdict"))

    except (requests.RequestException, ValueError) as exc:
        st.warning(f"Could not load events: {exc}")
        bump_refresh_errors()


def _render_red_activity(config: DashboardConfig) -> None:
    st.subheader("Red Agent Activity")
    try:
        inj_payload = get_agent_json(config, "/mirror/injections?limit=50")
        injections: list[dict[str, Any]] = inj_payload.get("injections", [])
        if not injections:
            st.info("No injections logged yet.")
            return

        for item in injections:
            status = detected_status(item.get("detected"))
            status_class = status_css_class(status)
            attack_type = html.escape(str(item.get("attack_type") or "unknown"))
            raw_value = html.escape(str(item.get("raw_value") or "n/a"))
            injected_at = html.escape(str(item.get("injected_at") or "n/a"))
            st.markdown(
                f"""
                <div class='injection-item'>
                  <div><strong>{attack_type}</strong> · {raw_value}</div>
                  <div class='injection-time'>{injected_at}</div>
                  <div class='injection-origin'>Origin: Injected simulation (RED)</div>
                  <div class='{status_class}'>{status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except (requests.RequestException, ValueError) as exc:
        st.warning(f"Could not load injections: {exc}")
        bump_refresh_errors()
