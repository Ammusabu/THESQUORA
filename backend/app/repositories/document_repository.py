"""
PyMongo access layer for `documents`.

Key indexes used here (from Phase 2):
- owner_recent: (owner_id, upload_date desc) -> "my docs newest first"
- dept_category: (department, category)
- uniq_file_hash: blocks duplicate uploads
- text_title_summary: powers keyword search on title/summary
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.collections import DOCUMENTS
from app.database.mongo_client import get_db


def _serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    if "owner_id" in out:
        out["owner_id"] = str(out["owner_id"])
    return out


def insert_document(doc: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    result = db[DOCUMENTS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)  


def find_by_id(doc_id: str) -> dict[str, Any] | None:
    try:
        oid = ObjectId(doc_id)
    except Exception:
        return None
    doc = get_db()[DOCUMENTS].find_one({"_id": oid})
    return _serialize(doc)


def find_by_hash(file_hash: str, *, owner_id: str | None = None) -> dict[str, Any] | None:
    """
    Look up a document by content hash.

    `owner_id` scopes the search to a single user's library. Duplicate
    detection MUST pass `owner_id` so that User B can upload a file that
    User A already has (per-user dedupe, not global).

    Passing `owner_id=None` does a global lookup — only use this for
    administrative/debug purposes; the upload path must always pass it.
    """
    query: dict[str, Any] = {"file_hash": file_hash}
    if owner_id is not None:
        try:
            query["owner_id"] = ObjectId(owner_id)
        except Exception:
            return None
    doc = get_db()[DOCUMENTS].find_one(query)
    return _serialize(doc)


def list_documents(
    *,
    user_id: str,
    role: str,
    page: int,
    limit: int,
    category: str | None = None,
    department: str | None = None,
    q: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Return (items, total). Access rule:
      - admin: sees all documents
      - user:  sees only their own
    Filters stack with $and.
    """
    db = get_db()
    conds: dict[str, Any] = {}
    if role != "admin":
        conds["owner_id"] = ObjectId(user_id)
    if category:
        conds["category"] = category
    if department:
        conds["department"] = department
    if q:
        # uses text index; $text requires a text search, not regex
        conds["$text"] = {"$search": q}

    total = db[DOCUMENTS].count_documents(conds)
    cursor = (
        db[DOCUMENTS]
        .find(conds)
        .sort("upload_date", DESCENDING)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    return [_serialize(d) for d in cursor], total  # type: ignore[misc]


def update_processing(
    doc_id: str,
    *,
    status: str,
    total_chunks: int | None = None,
    error: str | None = None,
) -> None:
    update: dict[str, Any] = {"processing_status": status}
    if total_chunks is not None:
        update["total_chunks"] = total_chunks
    if error is not None:
        update["error"] = error
    get_db()[DOCUMENTS].update_one(
        {"_id": ObjectId(doc_id)}, {"$set": update},
    )


def set_category(doc_id: str, category: str, confidence: float) -> None:
    get_db()[DOCUMENTS].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {
            "category": category,
            "classification_confidence": confidence,
        }},
    )


def delete_by_id(doc_id: str) -> bool:
    result = get_db()[DOCUMENTS].delete_one({"_id": ObjectId(doc_id)})
    return result.deleted_count == 1


def save_extracted_pages(doc_id: str, pages: list[str]) -> None:
    """
    Store extracted page texts alongside the document for downstream steps.
    Kept here (not in chunks) because chunking is a separate phase and we
    want the raw extracted text preserved even before embeddings.
    """
    get_db()[DOCUMENTS].update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"_extracted_pages": pages}},
    )


def compute_mean_embedding(document_id: str) -> list[float] | None:
    """
    Aggregate mean embedding across a document's chunks using $group + $avg.
    Then L2-normalize in Python so cosine == dot product (same as Phase 6).
    Returns None if the doc has no chunks or no embeddings.
    """
    import numpy as np
    from app.database.collections import CHUNKS

    try:
        oid = ObjectId(document_id)
    except Exception:
        return None

    pipeline = [
        {"$match": {"document_id": oid, "embedding": {"$exists": True, "$ne": None}}},
        {"$project": {"embedding": 1}},
    ]
    vecs = [row["embedding"] for row in get_db()[CHUNKS].aggregate(pipeline)]
    if not vecs:
        return None

    mean = np.asarray(vecs, dtype=np.float32).mean(axis=0)
    norm = float(np.linalg.norm(mean)) or 1.0
    return (mean / norm).astype(np.float32).tolist()


def set_cluster_id(document_id: str, cluster_id: int) -> None:
    get_db()[DOCUMENTS].update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {"cluster_id": int(cluster_id)}},
    )


def list_all_for_clustering(*, owner_filter: dict | None = None) -> list[dict]:
    """Return {id, title, category} for every processed document."""
    q = {"processing_status": "processed"}
    if owner_filter:
        q.update(owner_filter)
    cursor = get_db()[DOCUMENTS].find(q, {"title": 1, "category": 1, "total_chunks": 1})
    out = []
    for d in cursor:
        out.append({
            "id": str(d["_id"]),
            "title": d.get("title", ""),
            "category": d.get("category"),
            "total_chunks": d.get("total_chunks", 0),
        })
    return out
