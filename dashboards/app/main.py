from __future__ import annotations

import time

from .components import render_flow_legend, render_hero, render_signal_banner
from .config import load_config
from .sections import render_control_strip, render_feed_panels
from .sidebar import render_sidebar
from .state import bootstrap_state, get_refresh_error_count
from .theme import inject_global_theme

st = __import__("streamlit")


def run_dashboard() -> None:
    config = load_config()
    st.set_page_config(page_title="SPECTER", layout="wide")

    bootstrap_state()
    controls = render_sidebar(config)

    inject_global_theme()
    render_signal_banner()
    render_flow_legend()
    render_hero()

    render_control_strip(config, controls)
    render_feed_panels(config)

    if controls.auto_refresh_seconds > 0 and not config.disable_auto_refresh:
        penalty_multiplier = 2 ** min(get_refresh_error_count(), 3)
        next_refresh = min(controls.auto_refresh_seconds * penalty_multiplier, 60)
        st.caption(f"Auto-refresh active: next refresh in ~{next_refresh}s")
        time.sleep(next_refresh)
        st.rerun()
