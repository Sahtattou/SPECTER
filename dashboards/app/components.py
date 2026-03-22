from __future__ import annotations

st = __import__("streamlit")


def render_signal_banner() -> None:
    st.markdown(
        """
        <div class='top-signal'>
          threat grid uplink active · blue telemetry stream synchronized · detector arbitration online
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>SPECTER // Cyber Operations Console</h1>
          <p>
            Monitor live telemetry, launch controlled red-team injections, verify detector verdicts,
            and export analyst-ready artifacts from a single command surface.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flow_legend() -> None:
    st.markdown(
        """
        <div class='panel'>
          <p class='panel-title'>Pipeline Signal Legend</p>
          <p class='intel-caption'>
            BLUE = Real telemetry ingestion · RED = Injected simulation challenge · DETECTOR = Verdict assignment.
          </p>
          <div class='hacker-note'>
            Verdict labels are text-first: Detected (Quarantined), Passed Validation,
            Missed Injection, Needs Review.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
