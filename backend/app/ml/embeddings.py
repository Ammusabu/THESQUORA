"""
Sentence-Transformer wrapper (singleton).

Why singleton?
- Loading `all-MiniLM-L6-v2` (~90 MB) takes several seconds on CPU.
- Model weights are read-only during inference — safe to reuse across threads.

Why normalize_embeddings=True?
- Cosine similarity == dot product for unit vectors.
- Atlas Vector Search has a `cosine` similarity option; normalizing keeps
  everything consistent regardless of similarity metric used.
"""
from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config.settings import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        # Sanity check dimensions match config
        dim = _model.get_sentence_embedding_dimension()
        if dim != settings.EMBEDDING_DIM:
            logger.warning(
                "Configured EMBEDDING_DIM=%d but model outputs %d — using model's %d",
                settings.EMBEDDING_DIM, dim, dim,
            )
        logger.info("Embedding model ready (dim=%d)", dim)
    return _model


def get_dimension() -> int:
    return int(_get_model().get_sentence_embedding_dimension())


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    """Encode a batch of texts to normalised float vectors."""
    texts = list(texts)
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(
        texts,
        batch_size=settings.EMBED_BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vecs, dtype=np.float32).tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
