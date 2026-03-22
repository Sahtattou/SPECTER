from __future__ import annotations

st = __import__("streamlit")


def inject_global_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg-0: #020508;
          --bg-1: #061019;
          --bg-2: #0b1622;
          --matrix-green: #5dffb1;
          --cyber-cyan: #36e2ff;
          --warning-amber: #ffcf5a;
          --danger-red: #ff5f73;
          --text-hi: #e7f7ff;
          --text-mid: #9ec6d9;
          --panel-bg: rgba(8, 20, 31, 0.78);
          --panel-border: rgba(66, 170, 194, 0.38);
          --radius-lg: 16px;
          --radius-md: 12px;
          --shadow-cyan: 0 0 0.7rem rgba(54, 226, 255, 0.2), 0 0 2rem rgba(54, 226, 255, 0.1);
          --shadow-green: 0 0 0.6rem rgba(93, 255, 177, 0.24), 0 0 1.4rem rgba(93, 255, 177, 0.12);
        }

        .stApp {
          background: radial-gradient(1100px 700px at 6% 8%, #112127 0%, transparent 50%),
                      radial-gradient(900px 600px at 92% 6%, #101633 0%, transparent 52%),
                      linear-gradient(145deg, var(--bg-2), var(--bg-1) 38%, var(--bg-0) 100%);
          color: var(--text-hi);
        }

        .top-signal {
          border: 1px solid rgba(90, 225, 255, 0.45);
          border-radius: var(--radius-md);
          margin: 0 0 0.8rem 0;
          padding: 0.45rem 0.9rem;
          background: linear-gradient(90deg, rgba(7, 22, 31, 0.85), rgba(5, 16, 24, 0.65));
          font-size: 0.82rem;
          letter-spacing: 0.03em;
          color: var(--cyber-cyan);
          box-shadow: var(--shadow-cyan);
          text-transform: uppercase;
        }

        .hero {
          border: 1px solid rgba(89, 255, 177, 0.3);
          border-radius: var(--radius-lg);
          padding: 1.15rem 1.25rem;
          margin-bottom: 0.85rem;
          background: linear-gradient(130deg, rgba(11, 34, 29, 0.54), rgba(11, 21, 40, 0.68));
          box-shadow: var(--shadow-green);
        }

        .hero h1 {
          margin: 0;
          color: var(--text-hi);
          font-size: 1.8rem;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          text-shadow: 0 0 1rem rgba(93, 255, 177, 0.28);
        }

        .hero p {
          margin: 0.4rem 0 0 0;
          color: var(--text-mid);
          line-height: 1.4;
          letter-spacing: 0.02em;
        }

        .panel {
          border: 1px solid var(--panel-border);
          border-radius: var(--radius-md);
          padding: 0.9rem 1rem;
          background: var(--panel-bg);
          box-shadow: 0 0 0.6rem rgba(54, 226, 255, 0.1);
        }

        .panel-title {
          margin: 0;
          font-size: 0.9rem;
          color: var(--cyber-cyan);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .intel-caption {
          margin-top: 0.35rem;
          color: #89b4c7;
          font-size: 0.8rem;
        }

        .hacker-note {
          border-left: 3px solid var(--cyber-cyan);
          background: rgba(6, 21, 29, 0.72);
          border-radius: 8px;
          padding: 0.62rem 0.78rem;
          margin-top: 0.62rem;
          color: #b8d5e4;
          font-size: 0.84rem;
        }

        .status-caught {
          color: var(--matrix-green);
          font-weight: 700;
          text-shadow: 0 0 0.5rem rgba(93, 255, 177, 0.3);
        }

        .status-missed {
          color: var(--danger-red);
          font-weight: 700;
          text-shadow: 0 0 0.45rem rgba(255, 95, 115, 0.25);
        }

        .status-pending {
          color: var(--warning-amber);
          font-weight: 700;
          text-shadow: 0 0 0.45rem rgba(255, 207, 90, 0.2);
        }

        .injection-item {
          margin-bottom: 0.55rem;
          border: 1px solid rgba(78, 143, 171, 0.34);
          border-radius: 10px;
          padding: 0.62rem 0.72rem;
          background: rgba(7, 18, 27, 0.72);
        }

        .injection-time {
          font-size: 0.82rem;
          color: #89aabd;
        }

        .injection-origin {
          font-size: 0.78rem;
          color: #aec7d4;
          letter-spacing: 0.03em;
          text-transform: uppercase;
        }

        section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(5, 17, 24, 0.95), rgba(3, 10, 15, 0.92));
          border-right: 1px solid rgba(70, 158, 186, 0.25);
        }

        h2, h3, h4 {
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
          color: var(--text-hi);
          text-shadow: 0 0 0.55rem rgba(54, 226, 255, 0.16);
        }

        div[data-testid="stDataFrame"] {
          border: 1px solid rgba(84, 164, 189, 0.28);
          border-radius: 10px;
          overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
