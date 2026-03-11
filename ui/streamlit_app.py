import httpx
import streamlit as st
import uuid

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import settings
from ui.components.chat import render_message
from ui.components.data_table import render_data_table
from ui.components.kpi_cards import render_kpi_section
from ui.components.styles import inject_styles
from ui.utils.api_client import call_backend

st.set_page_config(
    page_title="Portfolio Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

SAMPLE_QUERIES = [
    "What are my current holdings?",
    "Show top 5 gainers",
    "Show top 10 losers",
    "What is my total unrealized profit?",
    "Sector breakdown of my portfolio",
    "Show all Technology stocks",
    "Total invested vs current value",
    "Show ETF holdings",
    "Portfolio breakdown by value",
    "My best performing stocks",
    "What are my Healthcare holdings?",
    "Show Conservative Portfolio",
    "Total realized profit/loss",
    "Asset type breakdown",
    "Which sector has highest unrealized PnL?",
    "Show top 10 holdings by current value",
]

_WELCOME = (
    "Welcome to **Portfolio Intelligence**. I have access to "
    "**10,000 financial records** across equities, ETFs, bonds, and REITs. "
    "Ask me anything about your holdings — profits, sector breakdowns, top gainers, and more."
)


def _init_session() -> None:
    st.session_state.setdefault("pill_counter", 0)
    st.session_state.setdefault("pending_query", None)
    st.session_state.setdefault("session_id", str(uuid.uuid4())[:8])
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": _WELCOME,
             "intent": "SYSTEM READY", "sql": None,
             "data": None, "latency_ms": None, "cache_hit": False}
        ]


def _handle_query(query: str) -> None:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.status("Querying database…", expanded=False) as status:
        try:
            result = call_backend(query, st.session_state.session_id)
            status.update(label="Done", state="complete", expanded=False)
            st.session_state.messages.append({
                "role":       "assistant",
                "content":    result.get("summary", "Done."),
                "intent":     result.get("intent", ""),
                "sql":        result.get("sql", ""),
                "data":       result.get("data", []),
                "latency_ms": result.get("latency_ms"),
                "cache_hit":  result.get("cache_hit", False),
            })
        except httpx.HTTPStatusError as exc:
            status.update(label="Backend error", state="error", expanded=False)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ HTTP {exc.response.status_code}: {exc.response.text[:200]}",
                "intent": "ERROR", "sql": None, "data": [],
                "latency_ms": None, "cache_hit": False,
            })
        except Exception as exc:
            status.update(label="Error", state="error", expanded=False)
            st.session_state.messages.append({
                "role": "assistant", "content": f"❌ {str(exc)[:300]}",
                "intent": "ERROR", "sql": None, "data": [],
                "latency_ms": None, "cache_hit": False,
            })

    st.rerun()


def _render_sidebar() -> None:
    with st.sidebar:
        st.html("""
        <div style="padding:8px 0 16px;">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#3a5a72;letter-spacing:0.1em;">PORTFOLIO INTELLIGENCE</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;font-weight:600;color:#e8c150;">AI Query Engine</div>
        </div>
        """)

        render_kpi_section()

        st.markdown("---")
        st.html('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.62rem;color:#3a5a72;letter-spacing:0.08em;margin-bottom:8px;">SAMPLE QUERIES</div>')

        selected = st.pills(
            "Sample Queries",
            SAMPLE_QUERIES,
            key=f"pills_{st.session_state.pill_counter}",
            label_visibility="collapsed",
        )
        if selected:
            st.session_state.pill_counter += 1
            st.session_state.pending_query = selected
            st.rerun()

        st.markdown("---")
        st.html(f"""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2a3a4a;line-height:1.6;">
          <div>ENGINE: Gemini 2.5 Flash-Lite</div>
          <div>DB: Neon PostgreSQL (10K rows)</div>
          <div>TARGET LATENCY: ≤ 2s</div>
          <div style="margin-top:4px;color:#1e3248;">Backend: {settings.backend_url}</div>
        </div>
        """)


def _render_chat() -> None:
    st.html("""
    <div class="pf-header">
      <div>
        <span class="live-dot"></span>
        <span class="pf-title">PORTFOLIO INTELLIGENCE</span>
        <span style="margin-left:12px;" class="pf-subtitle">NATURAL LANGUAGE QUERY SYSTEM · v1.0</span>
      </div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:#3a5a72;">
        10,000 FINANCIAL RECORDS · GEMINI AI · NEON POSTGRESQL
      </div>
    </div>
    """)

    for msg in st.session_state.messages:
        render_message(msg)
        if msg["role"] == "assistant":
            render_data_table(msg.get("data") or [])
            if msg.get("sql"):
                with st.expander("🔍 View generated SQL", expanded=False):
                    st.html(f'<div class="sql-box">{msg["sql"]}</div>')


def main() -> None:
    _init_session()
    _render_sidebar()
    _render_chat()

    if st.session_state.pending_query:
        q = st.session_state.pending_query
        st.session_state.pending_query = None
        _handle_query(q)

    if user_input := st.chat_input("Ask anything about your portfolio…  e.g. 'Show top 5 tech stocks by unrealized gain'"):
        _handle_query(user_input)


main()
