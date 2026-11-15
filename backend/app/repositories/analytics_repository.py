"""
Analytics aggregation pipelines.

Design principles:
- Each function issues ONE aggregation pipeline per collection.
- All scoping (admin vs user) is done inside the pipeline via $match.
- Where two collections must be joined, we use $lookup and then $unwind.
- None of these use `.find()` + Python loops — that would defeat the point.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from app.database.collections import (
    DOCUMENTS, CHUNKS, SEARCH_LOGS, CONVERSATIONS, USERS, MESSAGES,
)
from app.database.mongo_client import get_db


# ---------- helpers ----------
def _scope(user_id: str, is_admin: bool, field: str = "owner_id") -> list:
    """Return a $match stage scoping to owner or all (admin)."""
    if is_admin:
        return [{"$match": {}}]
    return [{"$match": {field: ObjectId(user_id)}}]


# ---------- overview: all counts in ONE $facet ----------
def overview(user_id: str, is_admin: bool) -> dict[str, Any]:
    """
    $facet lets us compute multiple independent sub-pipelines in a single
    round-trip. We run $facet over DOCUMENTS so the base $match is on
    documents; for other collections we use $unionWith to splice them in.

    Alternative (used here for clarity): run one $facet against a small
    'control' collection -- since Mongo doesn't allow $facet on empty
    pipelines in older versions, we achieve the same by aggregating over
    DOCUMENTS with $facet and getting the doc/chunk counts there; for
    searches and conversations we issue two extra count_documents (still
    cheap — indexed). Kept simple and correct.
    """
    db = get_db()
    owner_match: dict = {} if is_admin else {"owner_id": ObjectId(user_id)}
    chunks_match: dict = {} if is_admin else {"owner_id": ObjectId(user_id)}
    logs_match: dict = {} if is_admin else {"user_id": ObjectId(user_id)}
    conv_match: dict = {} if is_admin else {"user_id": ObjectId(user_id)}

    # One $facet for docs + total chunks (both from documents.chunks count)
    doc_facet = list(db[DOCUMENTS].aggregate([
        {"$match": owner_match},
        {"$facet": {
            "total_documents": [{"$count": "n"}],
            "total_chunks": [{"$group": {"_id": None, "sum": {"$sum": "$total_chunks"}}}],
        }},
    ]))
    total_documents = (doc_facet[0]["total_documents"][0]["n"]
                       if doc_facet and doc_facet[0]["total_documents"] else 0)
    total_chunks = (doc_facet[0]["total_chunks"][0]["sum"]
                    if doc_facet and doc_facet[0]["total_chunks"] else 0)

    total_searches = db[SEARCH_LOGS].count_documents(logs_match)
    total_conversations = db[CONVERSATIONS].count_documents(conv_match)
    total_users = db[USERS].count_documents({})

    return {
        "total_documents": int(total_documents),
        "total_chunks": int(total_chunks or 0),
        "total_searches": int(total_searches),
        "total_conversations": int(total_conversations),
        "total_users": int(total_users),
    }


# ---------- categories: $group over chunks ----------
def by_category(user_id: str, is_admin: bool) -> list[dict[str, Any]]:
    db = get_db()
    match: dict = {} if is_admin else {"owner_id": ObjectId(user_id)}
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    rows = list(db[CHUNKS].aggregate(pipeline))
    return [
        {"category": (r["_id"] or "Unclassified"), "count": int(r["count"])}
        for r in rows
    ]


# ---------- search trends: $group by day, last 14 days ----------
def search_trends(user_id: str, is_admin: bool, days: int = 14) -> list[dict]:
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    match: dict = {"created_at": {"$gte": since}}
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {
                "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"},
            },
            "count": {"$sum": 1},
            "avg_latency_ms": {"$avg": "$latency_ms"},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "_id": 0,
            "date": "$_id",
            "count": 1,
            "avg_latency_ms": {"$round": ["$avg_latency_ms", 0]},
        }},
    ]
    return list(db[SEARCH_LOGS].aggregate(pipeline))


# ---------- popular documents: $unwind logs -> $group by doc id -> $lookup title ----------
def popular_documents(user_id: str, is_admin: bool, limit: int = 10) -> list[dict]:
    db = get_db()
    match: dict = {}
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$unwind": "$retrieved_document_ids"},
        {"$group": {
            "_id": "$retrieved_document_ids",
            "search_count": {"$sum": 1},
        }},
        {"$sort": {"search_count": -1}},
        {"$limit": limit},
        # $lookup joins to documents; $unwind flattens the single-item array
        {"$lookup": {
            "from": DOCUMENTS,
            "localField": "_id",
            "foreignField": "_id",
            "as": "doc",
        }},
        {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "document_id": {"$toString": "$_id"},
            "title": {"$ifNull": ["$doc.title", "(deleted)"]},
            "category": "$doc.category",
            "search_count": 1,
        }},
    ]
    return list(db[SEARCH_LOGS].aggregate(pipeline))


# ---------- unanswered: queries with zero results, grouped ----------
def unanswered_queries(user_id: str, is_admin: bool, limit: int = 10) -> list[dict]:
    """
    Live knowledge gaps.

    A "gap" is a query that:
      1. Was recently asked (last 30 days)
      2. Returned 0 results at the time
      3. STILL returns 0 results against the current corpus (re-checked now)

    The re-check is done by a cheap vector + keyword lookup (no reranker,
    no LLM) with the same permission filter the user would have at search
    time. This means the panel reflects the CURRENT state of the knowledge
    base, not stale historical misses. In practice this is what an ops
    dashboard needs: "what can't we answer TODAY?"

    Cost: for 10 candidate gaps, ~10 * 2 retrievals. Small — but still
    cheap enough to run on request.
    """
    from datetime import timedelta
    from app.ml.embeddings import embed_text
    from app.repositories import chunk_repository as chunks_repo

    db = get_db()
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=30)

    # If the user has no processed docs, there are no "gaps" to show.
    doc_match: dict = {"processing_status": "processed"}
    if not is_admin:
        doc_match["owner_id"] = ObjectId(user_id)
    if db[DOCUMENTS].count_documents(doc_match) == 0:
        return []

    # Gather recent 0-result queries, deduplicated by query text.
    match: dict = {"result_count": 0, "created_at": {"$gte": since}}
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$query",
            "times": {"$sum": 1},
            "last_seen": {"$max": "$created_at"},
        }},
        {"$sort": {"last_seen": -1}},
        {"$limit": limit * 4},  # over-fetch: we'll filter many out
    ]
    rows = list(db[SEARCH_LOGS].aggregate(pipeline))
    if not rows:
        return []

    # Permission filter used for the re-check
    perm: dict | None = None
    if not is_admin:
        perm = {"owner_id": {"$eq": ObjectId(user_id)}}

    out: list[dict] = []
    for r in rows:
        q = r["_id"]
        if not q or not str(q).strip():
            continue

        # Re-check the query against the current corpus.
        still_empty = True
        try:
            # Use keyword search only to avoid loading the heavy embedding model
            # on the Render free tier (causes OOM crashes and 502 errors)
            k_hits = chunks_repo.keyword_search(
                query=q, limit=3, skip=0, filter_conditions=perm,
            )
            if k_hits:
                still_empty = False
        except Exception:
            still_empty = False

        if not still_empty:
            continue

        out.append({
            "query": q,
            "times": int(r["times"]),
            "last_seen": r["last_seen"].strftime("%Y-%m-%d %H:%M"),
        })
        if len(out) >= limit:
            break

    return out

def top_searched_categories(user_id: str, is_admin: bool, limit: int = 10) -> list[dict]:
    """
    For each search log, join retrieved_document_ids with documents, unwind,
    group by category. This tells us which categories users actually search
    for (which differs from which categories contain the most docs).
    """
    db = get_db()
    match: dict = {}
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$unwind": "$retrieved_document_ids"},
        {"$lookup": {
            "from": DOCUMENTS,
            "localField": "retrieved_document_ids",
            "foreignField": "_id",
            "as": "doc",
        }},
        {"$unwind": "$doc"},
        {"$group": {
            "_id": {"$ifNull": ["$doc.category", "Unclassified"]},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "category": "$_id", "count": 1}},
    ]
    return list(db[SEARCH_LOGS].aggregate(pipeline))


# ---------- ML classification performance ----------
def ml_performance(user_id: str, is_admin: bool) -> dict:
    """
    Aggregate classification outcomes + load training-time evaluation.

    The training-time metrics come from `ml/artifacts/metrics.json` which is
    written by scripts/train_classifier.py. If the file is missing, the
    `training` key is null — the frontend handles that gracefully.
    """
    import json
    from pathlib import Path as _Path

    db = get_db()
    match: dict = {"category": {"$ne": None}}
    if not is_admin:
        match["owner_id"] = ObjectId(user_id)

    # Per-category document counts + confidence distribution
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "avg_confidence": {"$avg": "$classification_confidence"},
            "min_confidence": {"$min": "$classification_confidence"},
            "max_confidence": {"$max": "$classification_confidence"},
        }},
        {"$sort": {"count": -1}},
    ]
    categories = []
    for r in db[DOCUMENTS].aggregate(pipeline):
        categories.append({
            "category": r["_id"],
            "count": int(r["count"]),
            "avg_confidence": round(float(r.get("avg_confidence") or 0), 3),
            "min_confidence": round(float(r.get("min_confidence") or 0), 3),
            "max_confidence": round(float(r.get("max_confidence") or 0), 3),
        })

    # High / mid / low confidence buckets
    bucket_pipeline = [
        {"$match": match},
        {"$bucket": {
            "groupBy": "$classification_confidence",
            "boundaries": [0, 0.5, 0.75, 1.001],
            "default": "other",
            "output": {"count": {"$sum": 1}},
        }},
    ]
    bucket_labels = {0: "low (<50%)", 0.5: "mid (50-75%)", 0.75: "high (>75%)"}
    buckets = []
    for r in db[DOCUMENTS].aggregate(bucket_pipeline):
        label = bucket_labels.get(r["_id"], "other")
        buckets.append({"bucket": label, "count": int(r["count"])})

    # Load training metrics (may not exist)
    training = None
    metrics_path = _Path(__file__).parents[1] / "ml" / "artifacts" / "metrics.json"
    if metrics_path.exists():
        try:
            data = json.loads(metrics_path.read_text())
            lr = data.get("logreg", {})
            nb = data.get("naive_bayes", {})
            training = {
                "n_train": data.get("n_train"),
                "n_test": data.get("n_test"),
                "classes": data.get("classes", []),
                "logreg_accuracy": lr.get("accuracy"),
                "logreg_macro_f1": (lr.get("report", {}).get("macro avg", {}) or {}).get("f1-score"),
                "nb_accuracy": nb.get("accuracy"),
                "nb_macro_f1": (nb.get("report", {}).get("macro avg", {}) or {}).get("f1-score"),
            }
        except Exception:
            training = None

    return {
        "categories": categories,
        "confidence_buckets": buckets,
        "training": training,
    }


# ---------- Search relevance metrics ----------
def search_relevance(user_id: str, is_admin: bool, days: int = 30) -> dict:
    """
    Quality signals for retrieval:
      - avg result count per query (higher = better recall)
      - zero-result rate (lower = better corpus coverage)
      - avg latency
      - breakdown by search mode (vector / keyword / hybrid)
    """
    from datetime import timedelta

    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    match: dict = {"created_at": {"$gte": since}}
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    # Overall stats
    overall_pipeline = [
        {"$match": match},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "avg_results": {"$avg": "$result_count"},
            "avg_latency": {"$avg": "$latency_ms"},
            "zero_results": {
                "$sum": {"$cond": [{"$eq": ["$result_count", 0]}, 1, 0]},
            },
        }},
    ]
    overall_rows = list(db[SEARCH_LOGS].aggregate(overall_pipeline))
    if not overall_rows:
        return {
            "total_searches": 0,
            "avg_results": 0,
            "avg_latency_ms": 0,
            "zero_result_rate": 0,
            "by_mode": [],
        }
    o = overall_rows[0]
    total = int(o["total"])
    zero = int(o["zero_results"])

    # Per-mode breakdown
    mode_pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$mode",
            "count": {"$sum": 1},
            "avg_results": {"$avg": "$result_count"},
            "avg_latency": {"$avg": "$latency_ms"},
        }},
        {"$sort": {"count": -1}},
    ]
    by_mode = []
    for r in db[SEARCH_LOGS].aggregate(mode_pipeline):
        by_mode.append({
            "mode": r["_id"] or "vector",
            "count": int(r["count"]),
            "avg_results": round(float(r.get("avg_results") or 0), 2),
            "avg_latency_ms": int(round(float(r.get("avg_latency") or 0))),
        })

    return {
        "total_searches": total,
        "avg_results": round(float(o.get("avg_results") or 0), 2),
        "avg_latency_ms": int(round(float(o.get("avg_latency") or 0))),
        "zero_result_rate": round((zero / total) * 100, 1) if total else 0.0,
        "by_mode": by_mode,
    }


# ---------- Unanswered query trends (weekly buckets) ----------
def unanswered_trends(user_id: str, is_admin: bool, days: int = 60) -> list[dict]:
    """
    Unanswered queries over time. Uses $dateTrunc (weekly bucket) so the
    frontend can chart whether knowledge gaps are shrinking or growing.
    """
    from datetime import timedelta

    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    match: dict = {
        "result_count": 0,
        "created_at": {"$gte": since},
    }
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {
                "$dateTrunc": {"date": "$created_at", "unit": "week"},
            },
            "count": {"$sum": 1},
            "unique_queries": {"$addToSet": "$query"},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "_id": 0,
            "week": {"$dateToString": {"format": "%Y-%m-%d", "date": "$_id"}},
            "count": 1,
            "unique_queries": {"$size": "$unique_queries"},
        }},
    ]
    return list(db[SEARCH_LOGS].aggregate(pipeline))


# ---------- Most useful documents (feedback-weighted) ----------
def most_useful_documents(user_id: str, is_admin: bool, limit: int = 10) -> list[dict]:
    """
    Rank documents by "usefulness" = how often they were cited in an answer
    that received a thumbs-up, minus thumbs-down. Score = up_count - down_count.

    This uses `messages.source_references` (embedded array) joined to
    `documents`, filtered on `feedback`. It's a genuinely useful signal:
    "which documents actually help users get answers?"
    """
    db = get_db()
    # Scope by message user (messages has user_id, not owner_id)
    match: dict = {
        "role": "assistant",
        "feedback": {"$in": ["up", "down"]},
    }
    if not is_admin:
        match["user_id"] = ObjectId(user_id)

    pipeline = [
        {"$match": match},
        {"$unwind": "$source_references"},
        {"$group": {
            "_id": "$source_references.document_id",
            "up": {"$sum": {"$cond": [{"$eq": ["$feedback", "up"]}, 1, 0]}},
            "down": {"$sum": {"$cond": [{"$eq": ["$feedback", "down"]}, 1, 0]}},
            "total": {"$sum": 1},
        }},
        {"$addFields": {
            "net_score": {"$subtract": ["$up", "$down"]},
        }},
        {"$sort": {"net_score": -1, "total": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": DOCUMENTS,
            "localField": "_id",
            "foreignField": "_id",
            "as": "doc",
        }},
        {"$unwind": {"path": "$doc", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "document_id": {"$toString": "$_id"},
            "title": {"$ifNull": ["$doc.title", "(deleted)"]},
            "category": "$doc.category",
            "up": 1,
            "down": 1,
            "total": 1,
            "net_score": 1,
        }},
    ]
    return list(db[MESSAGES].aggregate(pipeline))
