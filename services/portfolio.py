import asyncio
import time

from core.config import settings
from db.sessions import fetch_one_row, sync_cursor

_SQL_PG = """
    SELECT
        COUNT(*)                                AS total_records,
        COUNT(DISTINCT ticker)                  AS unique_instruments,
        COUNT(DISTINCT portfolio_name)          AS portfolios,
        COUNT(DISTINCT sector)                  AS sectors,
        ROUND(SUM(current_value)::numeric,  2)  AS total_aum,
        ROUND(SUM(invested_value)::numeric, 2)  AS total_invested,
        ROUND(SUM(unrealized_pnl)::numeric, 2)  AS total_unrealized_pnl,
        ROUND(SUM(realized_pnl)::numeric,   2)  AS total_realized_pnl,
        ROUND(AVG(unrealized_pnl)::numeric, 2)  AS avg_unrealized_pnl
    FROM holdings
"""

_SQL_LITE = """
    SELECT
        COUNT(*)                        AS total_records,
        COUNT(DISTINCT ticker)          AS unique_instruments,
        COUNT(DISTINCT portfolio_name)  AS portfolios,
        COUNT(DISTINCT sector)          AS sectors,
        ROUND(SUM(current_value),  2)   AS total_aum,
        ROUND(SUM(invested_value), 2)   AS total_invested,
        ROUND(SUM(unrealized_pnl), 2)   AS total_unrealized_pnl,
        ROUND(SUM(realized_pnl),   2)   AS total_realized_pnl,
        ROUND(AVG(unrealized_pnl), 2)   AS avg_unrealized_pnl
    FROM holdings
"""

_KEYS = [
    "total_records", "unique_instruments", "portfolios", "sectors",
    "total_aum", "total_invested", "total_unrealized_pnl",
    "total_realized_pnl", "avg_unrealized_pnl",
]

_cache: dict | None = None
_cache_ts: float = 0.0


async def get_stats() -> dict:
    global _cache, _cache_ts

    now = time.monotonic()
    if _cache is not None and (now - _cache_ts) < settings.stats_cache_ttl:
        return _cache

    if settings.use_postgres:
        result = await fetch_one_row(_SQL_PG) or {}
    else:
        def _sync() -> dict:
            with sync_cursor() as (_, cur):
                cur.execute(_SQL_LITE)
                return dict(zip(_KEYS, cur.fetchone()))
        result = await asyncio.to_thread(_sync)

    _cache, _cache_ts = result, now
    return result
