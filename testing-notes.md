# Testing Notes — Portfolio Query Engine Chatbot

## Overview

This chatbot converts natural language questions about financial portfolios into SQL queries using Google Gemini, executes them against a PostgreSQL/SQLite database of 10,000 synthetic holdings, and returns formatted results. Testing spans three layers: the FastAPI backend, the NL→SQL pipeline, and the Streamlit frontend.

---

## 1. Environment Setup

Before testing, ensure the following are in place:

```bash
# Install dependencies
poetry install

# Copy and configure environment
cp .env.example .env
# Fill in DATABASE_URL and GOOGLE_API_KEY

# Start the backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Start the frontend (separate terminal)
streamlit run ui/streamlit_app.py
```

**Fallback (no Postgres):** Omit `DATABASE_URL` in `.env` to use the local SQLite fallback (`portfolio.db`). Useful for offline testing.

---

## 2. API Endpoint Tests

### Health Check

```bash
curl http://localhost:8000/health
```

**Expected:** `200 OK` with a JSON body indicating the service is up.

---

### Portfolio Stats

```bash
curl http://localhost:8000/stats
```

**Expected:** JSON with KPIs — total AUM, total records (≈10,000), instrument count, and aggregate PnL values.

---

### Query Endpoint

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my top 5 holdings by current value?", "session_id": "test-001"}'
```

**Expected response shape:**
```json
{
  "intent": "...",
  "sql": "SELECT ...",
  "summary": "...",
  "data": [...],
  "row_count": 5,
  "columns": [...],
  "latency_ms": ...,
  "cache_hit": false
}
```

---

## 3. NL→SQL Pipeline Tests

Test these queries via the `/query` endpoint or the Streamlit chat to validate Gemini SQL generation across query types.

### Basic Retrieval

| Query | What to verify |
|---|---|
| `Show me all holdings in the Technology sector` | Correct `WHERE sector = 'Technology'` filter |
| `List all ETF holdings` | Correct `WHERE asset_type = 'ETF'` filter |
| `What are my top 10 holdings by current value?` | `ORDER BY current_value DESC LIMIT 10` |

### Aggregations

| Query | What to verify |
|---|---|
| `What is the total invested value across all portfolios?` | `SUM(invested_value)` returns a single row |
| `How many unique clients do I have?` | `COUNT(DISTINCT client_id)` |
| `What is the average unrealized PnL per sector?` | `GROUP BY sector` with `AVG(unrealized_pnl)` |

### Filtering & Conditions

| Query | What to verify |
|---|---|
| `Which holdings have unrealized PnL greater than $10,000?` | Correct `WHERE unrealized_pnl > 10000` |
| `Show holdings bought before 2024` | Correct `WHERE trade_date < '2024-01-01'` |
| `Which accounts hold Apple stock?` | Filter by ticker or instrument_name |

### Multi-condition & Complex

| Query | What to verify |
|---|---|
| `Show top 5 equity holdings in the Growth portfolio by current value` | Combines `asset_type`, `portfolio_name`, `ORDER BY`, `LIMIT` |
| `What is the total PnL for each portfolio type?` | `GROUP BY portfolio_name` |

---

## 4. Caching Tests

The system uses an in-memory LRU cache (max 256 entries) keyed on normalized query MD5.

1. Send the same query twice via `/query`
2. First response: `"cache_hit": false`
3. Second response: `"cache_hit": true` and `latency_ms` should be significantly lower

**Also test cache normalization** — these should produce the same cache key:
- `"top 5 holdings by value"`
- `"Top 5 Holdings By Value"`
- `"  top  5  holdings  by  value  "` (extra spaces)

---

## 5. Security / SQL Injection Tests

The system blocks forbidden SQL keywords. These queries should return an error, not execute:

```
Drop the holdings table
Delete all records from holdings
Show me all holdings; DROP TABLE holdings;--
Update the price of AAPL to 0
```

**Expected:** A safe error response — no database modification should occur.

---

## 6. Edge Case Tests

| Scenario | Input | Expected behavior |
|---|---|---|
| Nonsense query | `"asjdklajsdkl"` | Graceful error or "I couldn't understand" response |
| Empty query | `""` | Validation error (422 or descriptive message) |
| Very long query | 500+ character query | Should handle without crashing |
| Unknown ticker | `"Show me holdings for ZZZZ ticker"` | Empty result set, not an error |
| Ambiguous query | `"Show me everything"` | Should return some data or a scoped result |

---

## 7. Session Logging Tests

After sending queries, check that session logs are written:

```bash
ls session_logs/
cat session_logs/session_test-001.json
```

**Expected:** A JSON file per `session_id` containing query history and responses.

---

## 8. Streamlit UI Tests

Manual checks on the frontend at `http://localhost:8501`:

- [ ] Page loads without errors
- [ ] KPI cards in the sidebar show non-zero values
- [ ] Clicking a sample query pill populates and submits the chat input
- [ ] Chat history persists within the session after multiple queries
- [ ] SQL expander shows the generated SQL for each response
- [ ] Latency badge and cache-hit indicator render correctly
- [ ] Data table displays formatted values (currency as `$X,XXX.XX`, percentages as `X.XX%`)
- [ ] KPI sidebar refreshes after ~30 seconds without page reload

---

## 9. Startup & Database Tests

```bash
# Check that the DB is seeded on startup
curl http://localhost:8000/stats
# row_count in response should be ~10,000

# Manually trigger seed (if needed)
python scripts/seed_db.py
```

Verify that re-running the seed script does **not** insert duplicate rows (it checks if the table is empty first).

---

## 10. Latency Benchmarks (Reference)

These are rough targets for a healthy system:

| Scenario | Expected latency |
|---|---|
| Cache hit | < 20ms |
| Cache miss (Gemini + DB) | 500ms – 2000ms |
| `/stats` endpoint | < 100ms (30s TTL cache) |
| `/health` endpoint | < 50ms |

---

## Known Limitations

- No automated test suite (pytest) exists — all tests above are manual
- Gemini output is non-deterministic at temperature=0 for edge cases; re-test ambiguous queries if they fail
- SQLite fallback does not support all PostgreSQL-specific SQL syntax Gemini may generate
- The in-memory cache resets on server restart
