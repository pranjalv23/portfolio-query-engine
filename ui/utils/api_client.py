import httpx
import streamlit as st

from core.config import settings

_http = httpx.Client(
    base_url=settings.backend_url,
    timeout=httpx.Timeout(20.0, connect=5.0),
    headers={"Content-Type": "application/json"},
)


@st.cache_data(ttl=30)
def fetch_stats() -> dict:
    try:
        r = _http.get("/stats")
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def call_backend(query: str) -> dict:
    r = _http.post("/query", json={"query": query})
    r.raise_for_status()
    return r.json()
