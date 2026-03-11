from pydantic import BaseModel, field_validator


class QueryRequest(BaseModel):
    query: str
    session_id: str
    @field_validator("query")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty.")
        return v.strip()


class QueryResponse(BaseModel):
    query: str
    intent: str
    sql: str
    summary: str
    data: list[dict]
    row_count: int
    columns: list[str]
    latency_ms: float
    cache_hit: bool = False
