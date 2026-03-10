from core.config import settings
from core.logging_helpers import get_logger
from db.sessions import sync_cursor, SQLITE_PATH

logger = get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS holdings (
    {pk},
    client_id           TEXT    NOT NULL,
    account_id          TEXT    NOT NULL,
    instrument_name     TEXT    NOT NULL,
    ticker              TEXT    NOT NULL,
    asset_type          TEXT    NOT NULL,
    sector              TEXT    NOT NULL,
    quantity            REAL    NOT NULL,
    average_buy_price   REAL    NOT NULL,
    current_price       REAL    NOT NULL,
    invested_value      REAL    NOT NULL,
    current_value       REAL    NOT NULL,
    unrealized_pnl      REAL    NOT NULL,
    realized_pnl        REAL    NOT NULL,
    trade_date          TEXT    NOT NULL,
    holding_date        TEXT    NOT NULL,
    portfolio_name      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ticker      ON holdings(ticker);
CREATE INDEX IF NOT EXISTS idx_sector      ON holdings(sector);
CREATE INDEX IF NOT EXISTS idx_asset_type  ON holdings(asset_type);
CREATE INDEX IF NOT EXISTS idx_portfolio   ON holdings(portfolio_name);
CREATE INDEX IF NOT EXISTS idx_client      ON holdings(client_id);
CREATE INDEX IF NOT EXISTS idx_unrealized  ON holdings(unrealized_pnl);
CREATE INDEX IF NOT EXISTS idx_current_val ON holdings(current_value);
"""


def init_db() -> None:
    pk = "id SERIAL PRIMARY KEY" if settings.use_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    ddl = _DDL.format(pk=pk)
    with sync_cursor() as (_, cur):
        for stmt in ddl.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
    label = "Neon PostgreSQL" if settings.use_postgres else f"SQLite @ {SQLITE_PATH}"
    logger.info("Schema ready (%s)", label)


def count_rows() -> int:
    with sync_cursor() as (_, cur):
        cur.execute("SELECT COUNT(*) FROM holdings")
        row = cur.fetchone()
        return row["count"] if isinstance(row, dict) else row[0]
