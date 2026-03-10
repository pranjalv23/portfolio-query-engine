import os
import random
from datetime import date, timedelta

from core.logging_helpers import get_logger
from db.database import count_rows
from db.sessions import get_sync_connection, sync_cursor

logger = get_logger(__name__)

INSTRUMENTS: list[tuple] = [
    ("Apple Inc.",            "AAPL",   "Technology",             "Equity", 178),
    ("Microsoft Corp.",       "MSFT",   "Technology",             "Equity", 415),
    ("NVIDIA Corp.",          "NVDA",   "Technology",             "Equity", 875),
    ("Alphabet Inc.",         "GOOGL",  "Technology",             "Equity", 172),
    ("Amazon.com Inc.",       "AMZN",   "Consumer Discretionary", "Equity", 186),
    ("Meta Platforms Inc.",   "META",   "Technology",             "Equity", 512),
    ("Tesla Inc.",            "TSLA",   "Consumer Discretionary", "Equity", 248),
    ("JPMorgan Chase & Co.",  "JPM",    "Financials",             "Equity", 215),
    ("Berkshire Hathaway B",  "BRK.B",  "Financials",             "Equity", 372),
    ("Johnson & Johnson",     "JNJ",    "Healthcare",             "Equity", 148),
    ("UnitedHealth Group",    "UNH",    "Healthcare",             "Equity", 522),
    ("ExxonMobil Corp.",      "XOM",    "Energy",                 "Equity", 112),
    ("Chevron Corp.",         "CVX",    "Energy",                 "Equity", 154),
    ("Procter & Gamble",      "PG",     "Consumer Staples",       "Equity", 165),
    ("Coca-Cola Co.",         "KO",     "Consumer Staples",       "Equity",  62),
    ("Walmart Inc.",          "WMT",    "Consumer Staples",       "Equity",  94),
    ("Home Depot Inc.",       "HD",     "Consumer Discretionary", "Equity", 388),
    ("Visa Inc.",             "V",      "Financials",             "Equity", 278),
    ("Mastercard Inc.",       "MA",     "Financials",             "Equity", 472),
    ("Adobe Inc.",            "ADBE",   "Technology",             "Equity", 545),
    ("Salesforce Inc.",       "CRM",    "Technology",             "Equity", 298),
    ("Netflix Inc.",          "NFLX",   "Communication Services", "Equity", 624),
    ("Pfizer Inc.",           "PFE",    "Healthcare",             "Equity",  28),
    ("Merck & Co.",           "MRK",    "Healthcare",             "Equity", 128),
    ("NextEra Energy",        "NEE",    "Utilities",              "Equity",  72),
    ("Duke Energy Corp.",     "DUK",    "Utilities",              "Equity",  98),
    ("Caterpillar Inc.",      "CAT",    "Industrials",            "Equity", 362),
    ("Boeing Co.",            "BA",     "Industrials",            "Equity", 178),
    ("3M Company",            "MMM",    "Industrials",            "Equity",  92),
    ("Costco Wholesale",      "COST",   "Consumer Staples",       "Equity", 912),
    ("Prologis Inc.",         "PLD",    "Real Estate",            "REIT",   124),
    ("Simon Property Group",  "SPG",    "Real Estate",            "REIT",   162),
    ("S&P 500 ETF",           "SPY",    "Diversified",            "ETF",    512),
    ("QQQ Nasdaq-100 ETF",    "QQQ",    "Technology",             "ETF",    442),
    ("iShares Core Bond ETF", "AGG",    "Fixed Income",           "ETF",     98),
    ("Vanguard Total Market", "VTI",    "Diversified",            "ETF",    248),
    ("Bitcoin ETF (iShares)", "IBIT",   "Crypto",                 "ETF",     38),
    ("SPDR Gold ETF",         "GLD",    "Commodities",            "ETF",    218),
    ("US Treasury 10Y Bond",  "UST10Y", "Fixed Income",           "Bond",    95),
    ("Corp Bond AAA Fund",    "CORP_A", "Fixed Income",           "Bond",   102),
]

PORTFOLIOS = [
    "Growth Portfolio", "Conservative Portfolio", "Tech Focus",
    "Dividend Income", "Balanced Fund", "ESG Portfolio", "Global Macro",
]

CLIENTS  = [f"CL{i:04d}"  for i in range(1, 101)]
ACCOUNTS = [f"ACC{i:04d}" for i in range(1, 201)]

TARGET_ROWS = 10_000
BATCH_SIZE  = 2_000

_COLS = (
    "client_id, account_id, instrument_name, ticker, asset_type, sector, "
    "quantity, average_buy_price, current_price, invested_value, current_value, "
    "unrealized_pnl, realized_pnl, trade_date, holding_date, portfolio_name"
)
_INSERT_LITE = f"INSERT INTO holdings ({_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"


def _rand_date(rng: random.Random, start: date, end: date) -> str:
    return (start + timedelta(days=rng.randint(0, (end - start).days))).isoformat()


def generate_rows(n: int = TARGET_ROWS, seed: int = 42) -> list[tuple]:
    rng, start, end = random.Random(seed), date(2022, 1, 1), date(2024, 12, 31)
    rows = []
    for _ in range(n):
        name, ticker, sector, asset_type, base = rng.choice(INSTRUMENTS)
        avg_buy       = round(base * rng.uniform(0.60, 1.40), 2)
        current_price = round(base * rng.uniform(0.55, 1.55), 2)
        quantity      = rng.randint(1, 500)
        invested      = round(quantity * avg_buy, 2)
        current       = round(quantity * current_price, 2)
        trade_date    = _rand_date(rng, start, end)
        rows.append((
            rng.choice(CLIENTS), rng.choice(ACCOUNTS),
            name, ticker, asset_type, sector, quantity,
            avg_buy, current_price, invested, current,
            round(current - invested, 2), round(rng.uniform(-8_000, 12_000), 2),
            trade_date, _rand_date(rng, date.fromisoformat(trade_date), end),
            rng.choice(PORTFOLIOS),
        ))
    return rows


def seed_if_empty() -> int:
    if count_rows() >= TARGET_ROWS:
        return 0

    logger.info("Generating %d synthetic records...", TARGET_ROWS)
    rows = generate_rows(TARGET_ROWS)

    from core.config import settings
    if settings.use_postgres:
        _seed_postgres(rows)
    else:
        _seed_sqlite(rows)

    return TARGET_ROWS


def _seed_postgres(rows: list[tuple]) -> None:
    import psycopg
    from core.config import settings

    with psycopg.connect(settings.database_url) as conn:
        with conn.copy(f"COPY holdings ({_COLS}) FROM STDIN") as copy:
            for i, row in enumerate(rows, 1):
                copy.write_row(row)
                if i % BATCH_SIZE == 0:
                    logger.info("%d/%d rows streamed", i, TARGET_ROWS)
        conn.commit()
    logger.info("COPY complete — %d rows committed.", TARGET_ROWS)


def _seed_sqlite(rows: list[tuple]) -> None:
    conn = get_sync_connection()
    try:
        cur = conn.cursor()
        for i in range(0, len(rows), BATCH_SIZE):
            cur.executemany(_INSERT_LITE, rows[i: i + BATCH_SIZE])
            conn.commit()
            logger.info("%d/%d rows committed", min(i + BATCH_SIZE, TARGET_ROWS), TARGET_ROWS)
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    inserted = seed_if_empty()
    print(f"Done — {inserted:,} rows inserted." if inserted else "Already seeded.")
