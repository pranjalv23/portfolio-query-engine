import sqlite3
import contextlib
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from core.config import settings
from core.logging_helpers import get_logger

logger = get_logger(__name__)

SQLITE_PATH = Path(__file__).parent.parent / "portfolio.db"

_pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    global _pool
    if not settings.use_postgres:
        return
    _pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=5,
        max_idle=300,
        kwargs={"row_factory": dict_row, "connect_timeout": 10},
        open=False,
    )
    await _pool.open(wait=True)
    logger.info("psycopg3 pool ready (min=2/max=5)")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Pool not initialised — await init_pool() first.")
    return _pool


async def fetch_rows(sql: str) -> tuple[list[str], list[dict]]:
    async with get_pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            rows = await cur.fetchall()
    if not rows:
        return [], []
    return list(rows[0].keys()), rows


async def fetch_one_row(sql: str) -> dict | None:
    async with get_pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return await cur.fetchone()


def get_sync_connection():
    if settings.use_postgres:
        import psycopg
        return psycopg.connect(settings.database_url, row_factory=dict_row)
    conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextlib.contextmanager
def sync_cursor():
    conn = get_sync_connection()
    try:
        cur = conn.cursor()
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
