"""
Retrieval with optional cross-encoder reranking.

Pipeline:
  query -> embed -> vector search top candidates -> cross-encoder rerank -> top_k
"""
from __future__ import annotations

import logging

from bson import ObjectId

from app.database.collections import DOCUMENTS
from app.database.mongo_client import get_db
from app.ml.embeddings import embed_text
from app.ml.reranker import rerank
from app.repositories import chunk_repository as chunks_repo

logger = logging.getLogger(__name__)


def _permission_filter(current_user: dict) -> dict | None:
    if current_user["role"] == "admin":
        return None
    return {"owner_id": {"$eq": ObjectId(current_user["id"])}}


def _attach_titles(chunks: list[dict]) -> None:
    ids = list({c["document_id"] for c in chunks})
    if not ids:
        return
    docs = {
        d["_id"]: d
        for d in get_db()[DOCUMENTS].find({"_id": {"$in": ids}}, {"title": 1})
    }
    for c in chunks:
        c["document_title"] = docs.get(c["document_id"], {}).get("title") or "(unknown)"


def retrieve(
    *,
    current_user: dict,
    query: str,
    top_k: int = 5,
    candidate_pool: int = 20,
    use_reranker: bool = True,
) -> list[dict]:
    """
    Returns up to top_k chunks the user is permitted to see.
    Retrieval is vector search; reranker (optional) reorders by precision.
    """
    qvec = embed_text(query)
    raw = chunks_repo.vector_search(
        query_vector=qvec,
        limit=candidate_pool,
        num_candidates=max(100, candidate_pool * 10),
        filter_conditions=_permission_filter(current_user),
    )
    _attach_titles(raw)

    if use_reranker and raw:
        return rerank(query, raw, top_k=top_k)

    return raw[:top_k]
