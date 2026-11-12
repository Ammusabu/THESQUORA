"""
Create (or update) the Atlas Vector Search index on chunks.embedding.

Run:
    python -m scripts.create_vector_index

Requires an Atlas M0+ cluster (vector search is a paid-tier feature; M0 free
tier DOES support it as of 2024 — but confirm at atlas UI -> your cluster ->
Atlas Search tab).

The index is idempotent: re-running with the same definition is a no-op;
re-running with a changed definition triggers an update.
"""
from __future__ import annotations

import logging
import time

from pymongo.errors import OperationFailure

from app.config.logging_config import configure_logging
from app.config.settings import settings
from app.database.collections import CHUNKS
from app.database.mongo_client import get_client, get_db

configure_logging()
logger = logging.getLogger(__name__)

INDEX_NAME = "chunks_vector_index"


def build_definition() -> dict:
    """
    Vector field = `embedding` (384-d, cosine).
    Filter fields allow $vectorSearch.filter to operate on metadata BEFORE
    the ANN search (pre-filter), which is essential for permission-scoped
    retrieval.
    """
    return {
        "name": INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": settings.EMBEDDING_DIM,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "owner_id"},
                {"type": "filter", "path": "category"},
                {"type": "filter", "path": "department"},
                {"type": "filter", "path": "document_id"},
            ]
        },
    }


def _existing_indexes(db) -> list[dict]:
    try:
        return list(db[CHUNKS].list_search_indexes())
    except (OperationFailure, AttributeError) as exc:
        logger.error("Cannot list search indexes: %s", exc)
        return []


def create_or_update() -> None:
    db = get_db()
    definition = build_definition()

    existing = {ix["name"]: ix for ix in _existing_indexes(db)}
    if INDEX_NAME in existing:
        logger.info("Index %s already exists — updating definition", INDEX_NAME)
        try:
            db[CHUNKS].update_search_index(
                name=INDEX_NAME, definition=definition["definition"],
            )
            logger.info("Update submitted")
        except OperationFailure as exc:
            logger.warning("Update failed (may be identical): %s", exc)
    else:
        logger.info("Creating search index %s ...", INDEX_NAME)
        try:
            db[CHUNKS].create_search_index(definition)
            logger.info("Create submitted")
        except OperationFailure as exc:
            logger.error("Create failed: %s", exc)
            raise


def wait_until_ready(timeout_s: int = 300, poll_s: int = 5) -> str:
    """Poll until the index status is READY or timeout."""
    db = get_db()
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for ix in _existing_indexes(db):
            if ix["name"] == INDEX_NAME:
                status = ix.get("status", "UNKNOWN")
                logger.info("Index %s status=%s", INDEX_NAME, status)
                if status == "READY":
                    return status
                if status == "FAILED":
                    raise SystemExit("Vector index build FAILED — check Atlas UI logs")
        time.sleep(poll_s)
    raise SystemExit("Timed out waiting for vector index to become READY")


if __name__ == "__main__":
    create_or_update()
    wait_until_ready()
    print("\n✅ Vector search index is READY.\n")
