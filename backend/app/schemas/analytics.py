from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_searches: int
    total_conversations: int
    total_users: int


class CategoryBucket(BaseModel):
    category: str
    count: int


class CategoryResponse(BaseModel):
    items: list[CategoryBucket]


class SearchTrendPoint(BaseModel):
    date: str
    count: int
    avg_latency_ms: int | float | None = None


class SearchTrendResponse(BaseModel):
    items: list[SearchTrendPoint]


class PopularDoc(BaseModel):
    document_id: str
    title: str
    category: str | None = None
    search_count: int


class PopularDocsResponse(BaseModel):
    items: list[PopularDoc]


class UnansweredItem(BaseModel):
    query: str
    times: int
    last_seen: str


class UnansweredResponse(BaseModel):
    items: list[UnansweredItem]


class TopCategoriesResponse(BaseModel):
    items: list[CategoryBucket]


# ---------- Phase 12 extensions ----------
from pydantic import BaseModel as _BM


class CategoryPerformance(_BM):
    category: str
    count: int
    avg_confidence: float
    min_confidence: float
    max_confidence: float


class ConfidenceBucket(_BM):
    bucket: str
    count: int


class TrainingMetrics(_BM):
    n_train: int | None = None
    n_test: int | None = None
    classes: list[str] = []
    logreg_accuracy: float | None = None
    logreg_macro_f1: float | None = None
    nb_accuracy: float | None = None
    nb_macro_f1: float | None = None


class MLPerformanceResponse(_BM):
    categories: list[CategoryPerformance]
    confidence_buckets: list[ConfidenceBucket]
    training: TrainingMetrics | None = None


class ModeStats(_BM):
    mode: str
    count: int
    avg_results: float
    avg_latency_ms: int


class SearchRelevanceResponse(_BM):
    total_searches: int
    avg_results: float
    avg_latency_ms: int
    zero_result_rate: float
    by_mode: list[ModeStats]


class UnansweredTrendPoint(_BM):
    week: str
    count: int
    unique_queries: int


class UnansweredTrendsResponse(_BM):
    items: list[UnansweredTrendPoint]


class UsefulDoc(_BM):
    document_id: str
    title: str
    category: str | None = None
    up: int
    down: int
    total: int
    net_score: int


class UsefulDocsResponse(_BM):
    items: list[UsefulDoc]
