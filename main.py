import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.logging_helpers import get_logger
from db.database import init_db
from db.sessions import init_pool, close_pool
from llm.llm_services import init_cache
from schemas.portfolio import PortfolioStats
from schemas.query import QueryRequest, QueryResponse
from scripts.seed_db import seed_if_empty
from services.portfolio import get_stats
from services.query_engine import process_nl_query, prewarm_cache

logger = get_logger(__name__)


def _blocking_startup() -> None:
    inserted = seed_if_empty()
    logger.info("Seed: %d rows inserted." if inserted else "Seed: already populated.", inserted)
    init_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Portfolio Intelligence API...")
    init_db()
    await init_pool()
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        await loop.run_in_executor(pool, _blocking_startup)
    asyncio.create_task(prewarm_cache())
    logger.info("API ready.")
    yield
    await close_pool()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Portfolio Intelligence API",
    description="Natural Language Portfolio Query System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "Portfolio Intelligence API"}


@app.get("/stats", response_model=PortfolioStats, tags=["Portfolio"])
async def portfolio_stats():
    return await get_stats()


@app.post("/query", response_model=QueryResponse, tags=["Portfolio"])
async def query_portfolio(req: QueryRequest):
    t0 = time.perf_counter()
    try:
        result = await process_nl_query(req.query, req.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    result["query"] = req.query
    return result
