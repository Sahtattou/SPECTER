from __future__ import annotations

from dataclasses import dataclass

from .config import DashboardConfig
from .state import get_last_refresh_success_at, get_refresh_error_count

st = __import__("streamlit")


@dataclass(frozen=True)
class SidebarControls:
    allow_live_actions: bool
    auto_refresh_seconds: int


def render_sidebar(config: DashboardConfig) -> SidebarControls:
    st.sidebar.header("Operator Controls")
    presentation_mode = False
    if config.disable_presentation_mode:
        st.sidebar.info("Presentation mode disabled by environment kill switch.")
    else:
        presentation_mode = st.sidebar.toggle("Presentation mode", value=False)

    allow_live_actions = st.sidebar.checkbox(
        "Allow live actions",
        value=not presentation_mode,
        help="Disable to run read-only presentation mode.",
    )

    if config.disable_auto_refresh:
        st.sidebar.info("Auto-refresh disabled by environment kill switch.")
        auto_refresh_seconds = 0
    else:
        auto_refresh_seconds = st.sidebar.selectbox(
            "Auto-refresh", [0, 5, 10, 15, 30], index=2
        )

    if auto_refresh_seconds == 0 and not config.disable_auto_refresh:
        st.sidebar.warning(
            "Auto-refresh is OFF. Set a non-zero interval to keep ingested data live."
        )

    st.sidebar.caption(f"Last successful refresh: {get_last_refresh_success_at()}")
    st.sidebar.caption(f"Refresh error count: {get_refresh_error_count()}")

    return SidebarControls(
        allow_live_actions=allow_live_actions,
        auto_refresh_seconds=auto_refresh_seconds,
    )
