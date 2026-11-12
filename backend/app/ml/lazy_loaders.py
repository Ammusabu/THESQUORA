"""
Lazy model loaders — only load heavy models when actually needed.
This avoids 2-minute cold-starts on Render by deferring model
initialization to the first request that needs it.
"""
import logging
import threading

logger = logging.getLogger(__name__)

_embedding_model = None
_embedding_lock = threading.Lock()


def get_embedding_model():
    """Load MiniLM only on first use (thread-safe)."""
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                logger.info("Loading MiniLM embedding model (first use)...")
                from sentence_transformers import SentenceTransformer
                from app.config.settings import settings
                _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info("MiniLM loaded")
    return _embedding_model
