import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

.stApp {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: #090e18 !important;
    color: #c4d8e8 !important;
}
.stApp * { box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }

.pf-header {
    background: #0c1420; border-bottom: 1px solid #1e3248;
    padding: 0.7rem 1.4rem; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 1rem; border-radius: 6px;
}
.pf-title { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; color: #e8c150; letter-spacing: 0.12em; }
.pf-subtitle { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #3a5a72; letter-spacing: 0.06em; }
.live-dot { display: inline-block; width: 8px; height: 8px; background: #3ecf6e; border-radius: 50%; box-shadow: 0 0 6px #3ecf6e; margin-right: 8px; }

section[data-testid="stSidebar"] { background: #0c1420 !important; border-right: 1px solid #1e3248 !important; }
section[data-testid="stSidebar"] * { color: #c4d8e8 !important; }

.kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px; }
.kpi-card { background: #0f1e2e; border: 1px solid #1e3248; border-radius: 6px; padding: 8px 12px; }
.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; color: #3a5a72; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; font-weight: 600; color: #e0ecf5; }
.kpi-value.positive { color: #3ecf6e; }
.kpi-value.negative { color: #e05c5c; }

.msg-user { background: #0f1e2e; border: 1px solid #1e3248; border-radius: 12px 12px 2px 12px; padding: 12px 16px; margin: 8px 0 8px 15%; font-size: 0.9rem; color: #c4d8e8; }
.msg-ai { background: #0b1825; border: 1px solid #162840; border-radius: 12px 12px 12px 2px; padding: 14px 18px; margin: 8px 15% 8px 0; }
.msg-ai-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.58rem; color: #3a5a72; letter-spacing: 0.1em; margin-bottom: 6px; }
.msg-intent { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #2e6a9a; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #162840; letter-spacing: 0.06em; }
.msg-summary { font-size: 0.88rem; line-height: 1.65; color: #c4d8e8; }
.msg-summary strong { color: #e8c150; }

.latency-badge { display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; padding: 2px 8px; border-radius: 10px; margin-left: 8px; vertical-align: middle; }
.latency-ok   { background: #0a2a18; color: #3ecf6e; border: 1px solid #1a5a30; }
.latency-warn { background: #2a1a08; color: #e8c150; border: 1px solid #5a3a10; }
.latency-hit  { background: #0a1a2a; color: #3a9ae0; border: 1px solid #1a4a70; }

.sql-box { background: #060d16; border: 1px solid #162840; border-radius: 6px; padding: 10px 14px; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #6a9ec0; white-space: pre-wrap; margin-top: 10px; }

[data-testid="stPillsButton"] { background: #0f1e2e !important; border: 1px solid #1e3248 !important; border-radius: 16px !important; color: #5a8aaa !important; font-size: 0.72rem !important; }
[data-testid="stPillsButton"]:hover { background: #1e3a52 !important; color: #c4d8e8 !important; border-color: #2e5a7a !important; }
[data-testid="stPillsButton"][aria-selected="true"] { background: #1e3a52 !important; color: #e8c150 !important; border-color: #e8c150 !important; }

[data-testid="stChatInput"] textarea { background: #0c1420 !important; border: 1px solid #1e3248 !important; color: #c4d8e8 !important; font-family: 'IBM Plex Sans', sans-serif !important; border-radius: 8px !important; }
[data-testid="stStatusWidget"] { background: #0c1420 !important; border: 1px solid #1e3248 !important; border-radius: 6px !important; color: #c4d8e8 !important; }
</style>
"""


def inject_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
