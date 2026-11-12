"""
Cross-encoder reranker.

Why cross-encoder over bi-encoder (our existing embeddings)?
- Bi-encoder (MiniLM) embeds query and chunk INDEPENDENTLY -> fast, scalable,
  but loses fine-grained interaction between the two.
- Cross-encoder reads (query, chunk) TOGETHER and outputs a single relevance
  score. Much more accurate on subtle questions, but O(candidates) forward
  passes -> only practical on a small candidate pool.

Strategy: retrieve 20 candidates by bi-encoder, rerank, keep top 5.
This is the industry-standard "recall then precision" pattern.
"""
from __future__ import annotations

import logging

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        logger.info("Loading reranker: %s", _MODEL_NAME)
        _model = CrossEncoder(_MODEL_NAME, max_length=512)
        logger.info("Reranker ready")
    return _model


def rerank(
    query: str,
    candidates: list[dict],
    *,
    text_key: str = "text",
    top_k: int = 5,
) -> list[dict]:
    """
    Score each candidate against the query and return the top_k.
    Adds a `rerank_score` field to each returned chunk.
    """
    if not candidates:
        return []
    model = _get_model()
    pairs = [(query, (c.get(text_key) or "")[:2000]) for c in candidates]
    scores = model.predict(pairs, show_progress_bar=False)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]
