"""
Search orchestration for three modes: vector, keyword, hybrid.
Each mode returns paginated results with a unified result schema.
All searches log to search_logs.
"""
import logging
import time
from typing import Any

from bson import ObjectId

from app.database.collections import DOCUMENTS, SEARCH_LOGS
from app.database.mongo_client import get_db
from app.ml.embeddings import embed_text
from app.ml.reranker import rerank
from app.repositories import chunk_repository as chunks_repo
from app.services.fusion import reciprocal_rank_fusion

logger = logging.getLogger(__name__)


# ---------- shared helpers ----------
def _build_filter(
    current_user: dict,
    *,
    category: str | None,
    department: str | None,
) -> dict | None:
    conds: list[dict] = []
    if current_user["role"] != "admin":
        conds.append({"owner_id": {"$eq": ObjectId(current_user["id"])}})
    if category:
        conds.append({"category": {"$eq": category}})
    if department:
        conds.append({"department": {"$eq": department}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _attach_doc_titles(chunks: list[dict]) -> None:
    doc_ids = list({c["document_id"] for c in chunks})
    if not doc_ids:
        return
    docs = {
        d["_id"]: d
        for d in get_db()[DOCUMENTS].find(
            {"_id": {"$in": doc_ids}},
            {"title": 1, "owner_id": 1},
        )
    }
    for c in chunks:
        d = docs.get(c["document_id"])
        c["document_title"] = d["title"] if d else "(deleted)"


def _normalise(c: dict) -> dict:
    """Map raw chunk-doc + score to the public result schema."""
    return {
        "chunk_id": str(c["_id"]),
        "document_id": str(c["document_id"]),
        "document_title": c.get("document_title") or "(unknown)",
        "chunk_index": c.get("chunk_index"),
        "page_number": c.get("page_number"),
        "text": c["text"],
        "category": c.get("category"),
        "department": c.get("department"),
        "score": round(float(c.get("score", c.get("rrf_score", 0.0))), 4),
        "rrf_score": round(float(c["rrf_score"]), 6) if "rrf_score" in c else None,
    }


def _log_search(
    *, user_id: str, query: str, doc_ids: list[str],
    latency_ms: int, mode: str,
) -> None:
    from datetime import datetime, timezone
    get_db()[SEARCH_LOGS].insert_one({
        "user_id": ObjectId(user_id),
        "query": query,
        "mode": mode,
        "retrieved_document_ids": [ObjectId(d) for d in doc_ids if d],
        "result_count": len(doc_ids),
        "latency_ms": latency_ms,
        "created_at": datetime.now(timezone.utc),
    })


# ---------- mode implementations ----------
def _vector_mode(
    *, query: str, query_vec: list[float], limit: int, skip: int,
    filter_conditions: dict | None,
) -> list[dict]:
    # Over-fetch a candidate pool, then cross-encoder rerank for precision
    fetch = max((limit + skip) * 4, 20)
    raw = chunks_repo.vector_search(
        query_vector=query_vec,
        limit=fetch,
        num_candidates=max(100, fetch * 10),
        filter_conditions=filter_conditions,
    )
    _attach_doc_titles(raw)
    if raw:
        raw = rerank(query, raw, top_k=limit + skip)
    return raw[skip: skip + limit]


def _keyword_mode(
    *, query: str, limit: int, skip: int,
    filter_conditions: dict | None,
) -> list[dict]:
    raw = chunks_repo.keyword_search(
        query=query, limit=limit, skip=skip,
        filter_conditions=filter_conditions,
    )
    _attach_doc_titles(raw)
    return raw


def _hybrid_mode(
    *, query: str, query_vec: list[float], limit: int, skip: int,
    filter_conditions: dict | None,
) -> list[dict]:
    # Fetch candidate pools sized generously for RRF.
    pool = max((limit + skip) * 4, 40)
    v_hits = chunks_repo.vector_search(
        query_vector=query_vec,
        limit=pool,
        num_candidates=max(200, pool * 10),
        filter_conditions=filter_conditions,
    )
    k_hits = chunks_repo.keyword_search(
        query=query, limit=pool, skip=0,
        filter_conditions=filter_conditions,
    )
    # Attach doc titles to each side before fusion so we don't lose them.
    _attach_doc_titles(v_hits)
    _attach_doc_titles(k_hits)

    # RRF expects a stable identifier present on every item.
    for h in v_hits:
        h["chunk_id"] = str(h["_id"])
    for h in k_hits:
        h["chunk_id"] = str(h["_id"])

    fused = reciprocal_rank_fusion(
        [v_hits, k_hits], key="chunk_id", top_k=limit + skip,
    )
    # Re-attach the chunk-doc's _id for _normalise()
    for f in fused:
        f["_id"] = ObjectId(f["chunk_id"])
    # Final precision pass: cross-encoder rerank on the fused set
    if fused:
        fused = rerank(query, fused, top_k=limit + skip)
    return fused[skip: skip + limit]


# ---------- public API ----------
def search(
    *,
    current_user: dict,
    query: str,
    mode: str,
    limit: int,
    offset: int,
    category: str | None,
    department: str | None,
) -> dict[str, Any]:
    started = time.perf_counter()
    query = (query or "").strip()
    if not query:
        return {"query": query, "mode": mode, "results": [], "count": 0,
                "offset": offset, "limit": limit, "latency_ms": 0}

    if mode not in ("vector", "keyword", "hybrid"):
        mode = "vector"

    filt = _build_filter(current_user, category=category, department=department)
    query_vec = embed_text(query) if mode in ("vector", "hybrid") else []

    if mode == "vector":
        raw = _vector_mode(query=query, query_vec=query_vec, limit=limit, skip=offset,
                           filter_conditions=filt)
    elif mode == "keyword":
        raw = _keyword_mode(query=query, limit=limit, skip=offset,
                            filter_conditions=filt)
    else:
        raw = _hybrid_mode(query=query, query_vec=query_vec, limit=limit,
                           skip=offset, filter_conditions=filt)

    results = [_normalise(c) for c in raw]
    latency_ms = int((time.perf_counter() - started) * 1000)

    doc_ids = list({r["document_id"] for r in results})
    _log_search(user_id=current_user["id"], query=query, doc_ids=doc_ids,
                latency_ms=latency_ms, mode=mode)

    return {
        "query": query,
        "mode": mode,
        "count": len(results),
        "offset": offset,
        "limit": limit,
        "latency_ms": latency_ms,
        "results": results,
    }


# ---------- history ----------
def history(*, current_user: dict, page: int, limit: int) -> dict[str, Any]:
    db = get_db()
    q: dict = {} if current_user["role"] == "admin" else {
        "user_id": ObjectId(current_user["id"])
    }
    total = db[SEARCH_LOGS].count_documents(q)
    cursor = (
        db[SEARCH_LOGS].find(q)
        .sort("created_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    items = []
    for log in cursor:
        items.append({
            "id": str(log["_id"]),
            "query": log["query"],
            "mode": log.get("mode", "vector"),
            "result_count": log.get("result_count", 0),
            "latency_ms": log.get("latency_ms"),
            "created_at": log["created_at"].isoformat(),
        })
    return {"items": items, "total": total, "page": page, "limit": limit}
