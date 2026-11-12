"""
Reciprocal Rank Fusion (RRF).

score(doc) = sum over each ranked list of  1 / (k + rank)
  - rank is 1-based
  - k = 60 is the canonical default from the original RRF paper (Cormack 2009)
  - higher score = better
This requires no tuning weights and is robust when the two retrievers have
incomparable score scales (cosine vs BM25).
"""
from __future__ import annotations

RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    *,
    key: str,
    top_k: int,
    k: int = RRF_K,
) -> list[dict]:
    """
    ranked_lists: list of result lists (each already sorted best-first).
    key:         field to identify the same item across lists (e.g. "chunk_id").
    top_k:       how many fused items to return.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            ident = item[key]
            scores[ident] = scores.get(ident, 0.0) + 1.0 / (k + rank)
            # keep the first-seen copy; downstream fields are identical
            items.setdefault(ident, item)

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    out: list[dict] = []
    for ident, sc in ordered:
        item = dict(items[ident])
        item["rrf_score"] = round(sc, 6)
        out.append(item)
    return out
