"""
PyMongo layer for `chunks`.

Every chunk denormalises (owner_id, category, department) so Phase 7 can
push permission filters directly into the vector search query, avoiding
a costly $lookup per result.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.database.collections import CHUNKS
from app.database.mongo_client import get_db


def delete_for_document(document_id: str) -> int:
    """Idempotent re-indexing: clear old chunks first."""
    try:
        oid = ObjectId(document_id)
    except Exception:
        return 0
    return get_db()[CHUNKS].delete_many({"document_id": oid}).deleted_count


def bulk_insert(
    document_id: str,
    chunks: list[dict[str, Any]],
    *,
    owner_id: str,
    category: str | None,
    department: str | None,
) -> int:
    """
    Insert chunks with denormalised permission fields.
    Each item must have: chunk_index, text, page_number, embedding.
    """
    if not chunks:
        return 0
    oid = ObjectId(document_id)
    owner_oid = ObjectId(owner_id)
    now = datetime.now(timezone.utc)
    docs = [
        {
            "document_id": oid,
            "chunk_index": int(c["chunk_index"]),
            "text": c["text"],
            "page_number": c.get("page_number"),
            "category": category,
            "department": department,
            "owner_id": owner_oid,
            "embedding": c["embedding"],
            "metadata": None,
            "created_at": now,
        }
        for c in chunks
    ]
    result = get_db()[CHUNKS].insert_many(docs, ordered=False)
    return len(result.inserted_ids)


def count_for_document(document_id: str) -> int:
    try:
        oid = ObjectId(document_id)
    except Exception:
        return 0
    return get_db()[CHUNKS].count_documents({"document_id": oid})


def list_for_document(document_id: str, *, limit: int = 50) -> list[dict]:
    try:
        oid = ObjectId(document_id)
    except Exception:
        return []
    cursor = (
        get_db()[CHUNKS]
        .find({"document_id": oid}, {"embedding": 0})  # don't ship vectors to UI
        .sort("chunk_index", 1)
        .limit(limit)
    )
    return list(cursor)


def vector_search(
    *,
    query_vector: list[float],
    limit: int = 10,
    num_candidates: int = 100,
    filter_conditions: dict | None = None,
    exclude_doc_id: str | None = None,
) -> list[dict]:
    """
    Run $vectorSearch on chunks.embedding.

    filter_conditions: a MongoDB match expression evaluated PRE-ANN-search.
    Only fields declared as "filter" on the index can be used here.

    Returns documents with a `score` (higher = more similar, cosine in [0,1]
    since our vectors are normalised).
    """
    from bson import ObjectId

    pipeline: list[dict] = [
        {
            "$vectorSearch": {
                "index": "chunks_vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": max(num_candidates, limit * 10),
                "limit": limit,
                **({"filter": filter_conditions} if filter_conditions else {}),
            }
        },
        {
            "$project": {
                "_id": 1,
                "document_id": 1,
                "chunk_index": 1,
                "text": 1,
                "page_number": 1,
                "category": 1,
                "department": 1,
                "owner_id": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    if exclude_doc_id:
        try:
            pipeline.append({"$match": {"document_id": {"$ne": ObjectId(exclude_doc_id)}}})
        except Exception:
            pass

    return list(get_db()[CHUNKS].aggregate(pipeline))


def keyword_search(
    *,
    query: str,
    limit: int = 10,
    skip: int = 0,
    filter_conditions: dict | None = None,
) -> list[dict]:
    """
    Chunk-level keyword search using $text.
    Uses the chunks_text index (BM25-style scoring via $meta textScore).
    Permission/category filters stack via $and.
    """
    if not (query or "").strip():
        return []

    base_match: dict = {"$text": {"$search": query}}
    if filter_conditions:
        match = {"$and": [base_match, filter_conditions]}
    else:
        match = base_match

    pipeline = [
        {"$match": match},
        {"$addFields": {"score": {"$meta": "textScore"}}},
        {"$sort": {"score": -1, "_id": 1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$project": {
            "_id": 1, "document_id": 1, "chunk_index": 1, "text": 1,
            "page_number": 1, "category": 1, "department": 1,
            "owner_id": 1, "score": 1,
        }},
    ]
    return list(get_db()[CHUNKS].aggregate(pipeline))


def vector_search_excluding_doc(
    *,
    query_vector: list[float],
    exclude_document_id: str,
    limit: int = 20,
    filter_conditions: dict | None = None,
) -> list[dict]:
    """
    Vector search on chunks, excluding a given document (so "similar docs"
    never returns the source doc itself).
    """
    from bson import ObjectId

    pipeline = [
        {
            "$vectorSearch": {
                "index": "chunks_vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": max(100, limit * 10),
                "limit": limit * 4,  # over-fetch because we drop the excluded doc
                **({"filter": filter_conditions} if filter_conditions else {}),
            }
        },
        {"$match": {"document_id": {"$ne": ObjectId(exclude_document_id)}}},
        {"$limit": limit},
        {"$project": {
            "_id": 1, "document_id": 1, "chunk_index": 1,
            "text": 1, "page_number": 1, "category": 1,
            "score": {"$meta": "vectorSearchScore"},
        }},
    ]
    return list(get_db()[CHUNKS].aggregate(pipeline))
