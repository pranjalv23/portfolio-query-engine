import re

import streamlit as st


def latency_badge(latency_ms: float | None, cache_hit: bool) -> str:
    if cache_hit:
        return '<span class="latency-badge latency-hit">⚡ cached</span>'
    if latency_ms is None:
        return ""
    cls = "latency-ok" if latency_ms <= 2000 else "latency-warn"
    return f'<span class="latency-badge {cls}">{latency_ms / 1000:.2f}s</span>'


def _bold_to_html(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def render_message(msg: dict) -> None:
    if msg["role"] == "user":
        st.html(f'<div class="msg-user">🧑 {msg["content"]}</div>')
        return

    badge       = latency_badge(msg.get("latency_ms"), msg.get("cache_hit", False))
    intent      = msg.get("intent", "")
    intent_html = (
        f'<div class="msg-intent">◈ {intent.upper()}</div>'
        if intent and intent != "SYSTEM READY" else ""
    )

    st.html(f"""
    <div class="msg-ai">
      <div class="msg-ai-label">◆ PORTFOLIO AI {badge}</div>
      {intent_html}
      <div class="msg-summary">{_bold_to_html(msg.get("content", ""))}</div>
    </div>
    """)
