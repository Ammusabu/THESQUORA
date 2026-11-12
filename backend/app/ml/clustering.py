"""
KMeans clustering over document mean embeddings.

Why KMeans?
- Fast, deterministic (with fixed random_state), simple to explain.
- Works well on small corpora (5-50 docs) which is our realistic case.
- Produces crisp cluster assignments for UI grouping.

We extract dominant terms per cluster with TF-IDF over chunk text — this tells
the user WHY a cluster is what it is ("HR", "Technical", "Research"...).

Rule of thumb for k: min(8, ceil(n_docs / 3)), and at least 2 clusters
if there are 3+ docs.
"""
from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from app.repositories import document_repository as doc_repo

logger = logging.getLogger(__name__)


def _choose_k(n: int) -> int:
    if n < 2:
        return 1
    if n < 6:
        return 2
    return min(8, max(2, math.ceil(n / 3)))


def dominant_terms_per_cluster(
    chunks_by_cluster: dict[int, list[str]], top_n: int = 6,
) -> dict[int, list[str]]:
    """
    Concatenate all chunk texts per cluster, then TF-IDF across clusters
    and pick the top-N highest-weighted terms per cluster.
    """
    if not chunks_by_cluster:
        return {}
    cluster_ids = sorted(chunks_by_cluster.keys())
    corpus = ["\n".join(chunks_by_cluster[cid]) for cid in cluster_ids]
    if not any(corpus):
        return {cid: [] for cid in cluster_ids}

    vec = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2),
        min_df=1,
    )
    X = vec.fit_transform(corpus)  # shape (num_clusters, vocab)
    terms = vec.get_feature_names_out()

    out: dict[int, list[str]] = {}
    for row_idx, cid in enumerate(cluster_ids):
        row = X[row_idx].toarray().ravel()
        top_idx = row.argsort()[::-1][:top_n]
        out[cid] = [str(terms[i]) for i in top_idx if row[i] > 0]
    return out


def run_clustering(*, current_user: dict) -> dict[str, Any]:
    """
    1. Load all processed docs (owner-scoped for non-admins).
    2. Compute mean embedding per doc.
    3. KMeans -> cluster_id per doc.
    4. Extract dominant terms per cluster.
    5. Persist cluster_id onto each document.
    6. Return clusters with representative docs.
    """
    owner_filter = None
    if current_user["role"] != "admin":
        from bson import ObjectId
        owner_filter = {"owner_id": ObjectId(current_user["id"])}

    docs = doc_repo.list_all_for_clustering(owner_filter=owner_filter)
    docs = [d for d in docs if d["total_chunks"] > 0]
    if len(docs) < 2:
        return {
            "clusters": [],
            "note": "Need at least 2 processed documents with chunks to cluster.",
        }

    # Gather mean vectors
    vecs: list[list[float]] = []
    kept_docs: list[dict] = []
    for d in docs:
        v = doc_repo.compute_mean_embedding(d["id"])
        if v is not None:
            vecs.append(v)
            kept_docs.append(d)

    if len(vecs) < 2:
        return {"clusters": [], "note": "Not enough documents with embeddings."}

    X = np.asarray(vecs, dtype=np.float32)
    k = min(_choose_k(len(kept_docs)), len(kept_docs))
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X)

    # Fetch chunk texts per cluster for term extraction
    from app.database.collections import CHUNKS
    from app.database.mongo_client import get_db
    from bson import ObjectId

    cluster_docs: dict[int, list[dict]] = {}
    for doc, label in zip(kept_docs, labels):
        label_int = int(label)
        cluster_docs.setdefault(label_int, []).append(doc)
        doc_repo.set_cluster_id(doc["id"], label_int)  # persist for UI

    # One query: all chunks for all docs in these clusters (text only)
    all_doc_ids = [ObjectId(d["id"]) for d in kept_docs]
    doc_id_to_cluster = {d["id"]: int(l) for d, l in zip(kept_docs, labels)}
    chunks_by_cluster_text: dict[int, list[str]] = {}
    for ch in get_db()[CHUNKS].find(
        {"document_id": {"$in": all_doc_ids}}, {"document_id": 1, "text": 1},
    ):
        cid = doc_id_to_cluster.get(str(ch["document_id"]))
        if cid is None:
            continue
        chunks_by_cluster_text.setdefault(cid, []).append(ch.get("text", ""))

    terms = dominant_terms_per_cluster(chunks_by_cluster_text)

    clusters = []
    for label, members in sorted(cluster_docs.items()):
        members_sorted = sorted(members, key=lambda d: d["title"])
        clusters.append({
            "cluster_id": label,
            "num_documents": len(members_sorted),
            "dominant_terms": terms.get(label, []),
            "documents": [
                {"id": m["id"], "title": m["title"], "category": m["category"]}
                for m in members_sorted
            ],
        })

    return {"clusters": clusters, "k": k, "docs_considered": len(kept_docs)}
