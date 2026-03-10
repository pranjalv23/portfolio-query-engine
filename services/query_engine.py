import math
import hashlib
import re

from core.config import settings
from core.logging_helpers import get_logger
from db.sessions import fetch_rows
from llm.llm_services import generate_sql

logger = get_logger(__name__)

_FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|INSERT|UPDATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

_MONEY_COLS = {
    "invested_value", "current_value", "unrealized_pnl", "realized_pnl",
    "average_buy_price", "current_price", "total_current_value",
    "total_invested", "total_unrealized_pnl", "total_realized_pnl",
    "avg_unrealized_pnl", "total_aum",
}
_MONEY_SUFFIXES = ("_value", "_pnl", "_price", "_aum", "_invested")
_PCT_COLS = {"return_pct", "pct_of_portfolio"}
_NAME_COLS = ("ticker", "instrument_name", "sector", "portfolio_name", "asset_type", "client_id")

_cache: dict[str, dict] = {}

_PREWARM_QUERIES = [
    "What are my current holdings?",
    "Show top 5 gainers",
    "Show top 10 losers",
    "What is my total unrealized profit?",
    "Sector breakdown of my portfolio",
    "Total invested vs current value",
    "Asset type breakdown",
]


def _cache_key(query: str) -> str:
    normalised = re.sub(r"\s+", " ", query.strip().lower())
    return hashlib.md5(normalised.encode()).hexdigest()


def _cache_get(query: str) -> dict | None:
    return _cache.get(_cache_key(query))


def _cache_set(query: str, result: dict) -> None:
    key = _cache_key(query)
    if len(_cache) >= settings.response_cache_max:
        _cache.pop(next(iter(_cache)))
    _cache[key] = {k: v for k, v in result.items() if k != "latency_ms"}


def _validate_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    if _FORBIDDEN.search(sql):
        raise ValueError("Query contains a forbidden SQL keyword.")
    if not sql.upper().lstrip().startswith("SELECT"):
        raise ValueError("Only SELECT queries are permitted.")
    return sql


def _fmt(col: str, val) -> str:
    if val is None:
        return "—"
    col_l = col.lower()
    if col_l in _MONEY_COLS or any(col_l.endswith(s) for s in _MONEY_SUFFIXES):
        try:
            v = float(val)
            sign = ("+" if v >= 0 else "-") if "pnl" in col_l else ""
            return f"{sign}${abs(v):,.2f}"
        except (TypeError, ValueError):
            pass
    if col_l.endswith("_pct") or col_l in _PCT_COLS:
        try:
            return f"{float(val):.2f}%"
        except (TypeError, ValueError):
            pass
    return str(val)


def _build_summary(intent: str, columns: list[str], rows: list[dict]) -> str:
    if not rows:
        return "No data found for your query."
    n = len(rows)
    if n == 1 and len(columns) <= 6:
        parts = [f"**{c.replace('_', ' ').title()}:** {_fmt(c, rows[0].get(c))}" for c in columns]
        return "  ·  ".join(parts)
    name_col = next((c for c in columns if c in _NAME_COLS), None)
    value_col = next((c for c in columns if "value" in c or "pnl" in c), None)
    if name_col and value_col:
        return (
            f"**{n} result{'s' if n != 1 else ''}** for \"{intent}\". "
            f"Top: **{rows[0].get(name_col, '')}** → {_fmt(value_col, rows[0].get(value_col))}."
        )
    return f"**{n} record{'s' if n != 1 else ''}** returned for \"{intent}\"."


async def process_nl_query(nl_query: str) -> dict:
    cached = _cache_get(nl_query)
    if cached is not None:
        return {**cached, "cache_hit": True}

    intent, raw_sql = await generate_sql(nl_query)
    sql = _validate_sql(raw_sql)

    columns, rows = await fetch_rows(sql)

    for row in rows:
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                row[k] = None

    result = {
        "intent": intent,
        "sql": sql,
        "summary": _build_summary(intent, columns, rows),
        "data": rows,
        "row_count": len(rows),
        "columns": columns,
        "cache_hit": False,
    }

    _cache_set(nl_query, result)
    return result


async def prewarm_cache() -> None:
    logger.info("Pre-warming response cache (%d queries)...", len(_PREWARM_QUERIES))
    for q in _PREWARM_QUERIES:
        if not _cache_get(q):
            try:
                result = await process_nl_query(q)
                _cache_set(q, result)
            except Exception as exc:
                logger.warning("Prewarm failed for %r: %s", q, exc)
    logger.info("Pre-warm complete — %d entries cached.", len(_cache))
