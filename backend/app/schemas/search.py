from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    mode: str = Field("vector", pattern="^(vector|keyword|hybrid)$")
    limit: int = Field(10, ge=1, le=50)
    offset: int = Field(0, ge=0)
    category: str | None = None
    department: str | None = None


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str | None
    chunk_index: int | None
    page_number: int | None
    text: str
    category: str | None
    department: str | None
    score: float
    rrf_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    mode: str
    count: int
    offset: int
    limit: int
    latency_ms: int
    results: list[SearchResult]


class SearchHistoryItem(BaseModel):
    id: str
    query: str
    mode: str
    result_count: int
    latency_ms: int | None
    created_at: datetime


class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryItem]
    total: int
    page: int
    limit: int
