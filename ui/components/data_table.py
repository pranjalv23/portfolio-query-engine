import pandas as pd
import streamlit as st

_MONEY_KWS = ("value", "pnl", "price", "invested", "aum")
_PCT_COLS  = {"return_pct", "pct_of_portfolio"}


def render_data_table(data: list[dict]) -> None:
    if not data:
        return

    df  = pd.DataFrame(data)
    cfg: dict[str, st.column_config.Column] = {}

    for col in df.columns:
        col_l = col.lower()
        title = col.replace("_", " ").title()
        if any(kw in col_l for kw in _MONEY_KWS):
            cfg[col] = st.column_config.NumberColumn(title, format="$%.2f")
        elif col_l.endswith("_pct") or col_l in _PCT_COLS:
            cfg[col] = st.column_config.NumberColumn(title, format="%.2f%%")

    st.dataframe(
        df,
        column_config=cfg,
        use_container_width=True,
        height=min(400, 40 + len(df) * 36),
    )
