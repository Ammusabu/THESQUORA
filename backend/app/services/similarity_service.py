"""
Similar-document detection.

Algorithm:
  1. Compute the target document's mean embedding (from its chunks).
  2. Vector-search chunks of all OTHER documents using that mean as the query.
  3. Group those chunk hits by document_id, aggregate a score per doc
     (max chunk score, or mean of top-k chunk scores).
  4. Return top-N docs with title, category, snippet, similarity score.
"""
import logging
from collections import defaultdict
from typing import Any

from bson import ObjectId
from fastapi import HTTPException

from app.database.collections import DOCUMENTS
from app.database.mongo_client import get_db
from app.repositories import chunk_repository as chunks_repo
from app.repositories import document_repository as doc_repo

logger = logging.getLogger(__name__)


def _permission_filter(current_user: dict) -> dict | None:
    if current_user["role"] == "admin":
        return None
    return {"owner_id": {"$eq": ObjectId(current_user["id"])}}


def similar_documents(
    *,
    document_id: str,
    current_user: dict,
    limit: int = 5,
) -> dict[str, Any]:
    target = doc_repo.find_by_id(document_id)
    if not target:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user["role"] != "admin" and target["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorised")

    mean_vec = doc_repo.compute_mean_embedding(document_id)
    if not mean_vec:
        return {"document": target, "similar": [], "note": "Document has no embeddings"}

    hits = chunks_repo.vector_search_excluding_doc(
        query_vector=mean_vec,
        exclude_document_id=document_id,
        limit=50,
        filter_conditions=_permission_filter(current_user),
    )

    # Per-document: take the max chunk score and remember the best snippet
    by_doc: dict[str, dict] = defaultdict(lambda: {"score": 0.0, "best": None})
    for h in hits:
        did = str(h["document_id"])
        score = float(h.get("score", 0.0))
        bucket = by_doc[did]
        if score > bucket["score"]:
            bucket["score"] = score
            bucket["best"] = h

    if not by_doc:
        return {"document": target, "similar": []}

    # Fetch doc metadata for the retrieved IDs in one round-trip
    oids = [ObjectId(d) for d in by_doc.keys()]
    docs_meta = {
        str(d["_id"]): d
        for d in get_db()[DOCUMENTS].find({"_id": {"$in": oids}})
    }

    results = []
    for did, bucket in by_doc.items():
        meta = docs_meta.get(did)
        if not meta:
            continue
        best = bucket["best"] or {}
        results.append({
            "document_id": did,
            "title": meta.get("title", "(unknown)"),
            "category": meta.get("category"),
            "department": meta.get("department"),
            "similarity": round(bucket["score"], 4),
            "matched_page": best.get("page_number"),
            "snippet": (best.get("text") or "")[:240],
        })

    results.sort(key=lambda r: r["similarity"], reverse=True)
    return {"document": target, "similar": results[:limit]}
