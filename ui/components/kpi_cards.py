import streamlit as st

from ui.utils.api_client import fetch_stats


def _fmt_millions(v, signed: bool = False) -> str:
    try:
        v = float(v)
        prefix = ("+" if v >= 0 else "-") if signed else ""
        return f"{prefix}${abs(v) / 1e6:,.1f}M"
    except (TypeError, ValueError):
        return "—"


@st.fragment(run_every=30)
def render_kpi_section() -> None:
    stats = fetch_stats()
    if not stats:
        st.caption("⚠️ Could not load portfolio stats.")
        return

    pnl  = float(stats.get("total_unrealized_pnl", 0) or 0)
    rpnl = float(stats.get("total_realized_pnl",   0) or 0)

    st.html(f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">RECORDS</div>
        <div class="kpi-value">{stats.get('total_records', 0):,}</div></div>
      <div class="kpi-card"><div class="kpi-label">INSTRUMENTS</div>
        <div class="kpi-value">{stats.get('unique_instruments', 0)}</div></div>
      <div class="kpi-card"><div class="kpi-label">TOTAL AUM</div>
        <div class="kpi-value">{_fmt_millions(stats.get('total_aum', 0))}</div></div>
      <div class="kpi-card"><div class="kpi-label">INVESTED</div>
        <div class="kpi-value">{_fmt_millions(stats.get('total_invested', 0))}</div></div>
      <div class="kpi-card" style="grid-column:span 2;">
        <div class="kpi-label">UNREALIZED P&L</div>
        <div class="kpi-value {'positive' if pnl >= 0 else 'negative'}">{_fmt_millions(pnl, signed=True)}</div>
      </div>
      <div class="kpi-card" style="grid-column:span 2;">
        <div class="kpi-label">REALIZED P&L</div>
        <div class="kpi-value {'positive' if rpnl >= 0 else 'negative'}">{_fmt_millions(rpnl, signed=True)}</div>
      </div>
    </div>
    """)
