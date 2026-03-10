import re
import json

from google import genai
from google.genai import types

from core.config import settings
from core.logging_helpers import get_logger

logger = get_logger(__name__)

_client = genai.Client(
    api_key=settings.google_api_key,
    http_options=types.HttpOptions(async_client_args={}),
)

SYSTEM_PROMPT = """
You are an expert financial data analyst and SQL engineer.
Your only job: convert the user's natural language question into a precise
PostgreSQL SELECT query and return the result as a compact JSON object.

════ DATABASE SCHEMA ════

Table: holdings   (10 000 rows of synthetic financial data)

  id                INTEGER  PK — never filter on this
  client_id         TEXT     CL0001–CL0100
  account_id        TEXT     ACC0001–ACC0200
  instrument_name   TEXT     Full name. Use LIKE '%keyword%' for partials.
  ticker            TEXT     UPPERCASE exact symbol. Examples:
                             AAPL MSFT NVDA GOOGL AMZN META TSLA JPM BRK.B
                             JNJ UNH XOM CVX PG KO WMT HD V MA ADBE CRM
                             NFLX PFE MRK NEE DUK CAT BA MMM COST PLD SPG
                             SPY QQQ AGG VTI IBIT GLD UST10Y CORP_A
  asset_type        TEXT     Equity | ETF | Bond | REIT
  sector            TEXT     Technology | Healthcare | Financials | Energy |
                             Consumer Discretionary | Consumer Staples |
                             Utilities | Real Estate | Industrials |
                             Communication Services | Fixed Income |
                             Diversified | Commodities | Crypto
  quantity          REAL     shares / units held (always positive)
  average_buy_price REAL     cost per unit (USD)
  current_price     REAL     market price per unit (USD)
  invested_value    REAL     quantity × average_buy_price
  current_value     REAL     quantity × current_price
  unrealized_pnl    REAL     current_value − invested_value
  realized_pnl      REAL     booked P&L (can be negative)
  trade_date        TEXT     YYYY-MM-DD  (2022-01-01 → 2024-12-31)
  holding_date      TEXT     YYYY-MM-DD  (≥ trade_date)
  portfolio_name    TEXT     "Growth Portfolio" | "Conservative Portfolio" |
                             "Tech Focus" | "Dividend Income" |
                             "Balanced Fund" | "ESG Portfolio" | "Global Macro"

Indexed: ticker, sector, asset_type, portfolio_name, client_id,
         unrealized_pnl, current_value

════ OUTPUT FORMAT ════

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "intent": "<≤12-word description of what the user wants>",
  "sql":    "<valid PostgreSQL SELECT statement>"
}

════ SQL RULES ════

1.  Row queries default to LIMIT 25 unless the user specifies a different N.
2.  Aggregation / breakdown queries: NO LIMIT.
3.  Top gainers  → ORDER BY unrealized_pnl DESC
4.  Top losers   → ORDER BY unrealized_pnl ASC
5.  Best return  → ORDER BY (current_value - invested_value)*100.0/invested_value DESC
6.  Always ROUND money: ROUND(SUM(col)::numeric, 2)
7.  Return %: ROUND((current_value - invested_value)*100.0/invested_value, 2)
8.  Breakdowns → GROUP BY with SUM / COUNT / ROUND aggregates.
9.  Aliases with spaces: SELECT SUM(x) AS "Total Value"
10. FORBIDDEN (never emit): DROP DELETE TRUNCATE INSERT UPDATE ALTER CREATE
    GRANT REVOKE — only SELECT is permitted.
"""

_cache_name: str | None = None


def init_cache() -> None:
    global _cache_name
    try:
        cache = _client.caches.create(
            model=settings.gemini_model,
            config=types.CreateCachedContentConfig(
                system_instruction=SYSTEM_PROMPT,
                display_name="portfolio-system-prompt",
                ttl="3600s",
            ),
        )
        _cache_name = cache.name
        logger.info("Gemini context cache created: %s", _cache_name)
    except Exception as exc:
        logger.warning("Gemini context cache failed: %s — running without cache.", exc)
        _cache_name = None


async def generate_sql(nl_query: str) -> tuple[str, str]:
    config_kwargs: dict = dict(
        temperature=0.0,
        max_output_tokens=180,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    if _cache_name:
        config_kwargs["cached_content"] = _cache_name
    else:
        config_kwargs["system_instruction"] = SYSTEM_PROMPT

    response = await _client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=nl_query,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {raw[:300]}") from exc

    return payload.get("intent", "portfolio query"), payload.get("sql", "")
