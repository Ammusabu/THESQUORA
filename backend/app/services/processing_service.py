"""
Full post-upload pipeline:
  extracted pages -> chunk -> embed -> insert -> update document status.

Idempotent: safe to re-run on the same document. We first delete existing
chunks for that doc, then rebuild.
"""
import logging
from typing import Any

from bson import ObjectId
from fastapi import HTTPException

from app.config.settings import settings
from app.database.collections import DOCUMENTS
from app.database.mongo_client import get_db
from app.ml.embeddings import embed_texts
from app.repositories import chunk_repository as chunks_repo
from app.repositories import document_repository as doc_repo
from app.services.chunking import chunk_pages

logger = logging.getLogger(__name__)


def _get_document_raw(document_id: str) -> dict | None:
    try:
        oid = ObjectId(document_id)
    except Exception:
        return None
    return get_db()[DOCUMENTS].find_one({"_id": oid})


def process_document(document_id: str) -> dict[str, Any]:
    doc = _get_document_raw(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = doc.get("_extracted_pages") or []
    if not pages:
        doc_repo.update_processing(document_id, status="failed",
                                   error="No extracted pages available")
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    # Clear old chunks (idempotent)
    chunks_repo.delete_for_document(document_id)

    # Chunk
    try:
        chunks = chunk_pages(
            pages,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
    except ValueError as exc:
        doc_repo.update_processing(document_id, status="failed", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

    if not chunks:
        doc_repo.update_processing(document_id, status="failed",
                                   error="No chunks produced")
        raise HTTPException(status_code=400, detail="No chunks produced from document")

    # Embed in one batch (MiniLM handles batches efficiently)
    texts = [c.text for c in chunks]
    try:
        vectors = embed_texts(texts)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Embedding failed: %s", exc)
        doc_repo.update_processing(document_id, status="failed",
                                   error=f"Embedding failed: {exc}")
        raise HTTPException(status_code=500, detail="Embedding failed")

    # Insert chunks (with denormalised permission fields)
    inserted = chunks_repo.bulk_insert(
        document_id,
        [
            {
                "chunk_index": c.chunk_index,
                "text": c.text,
                "page_number": c.page_number,
                "embedding": vec,
            }
            for c, vec in zip(chunks, vectors)
        ],
        owner_id=str(doc["owner_id"]),
        category=doc.get("category"),
        department=doc.get("department"),
    )

    # Finalise the document
    get_db()[DOCUMENTS].update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "processing_status": "processed",
                "total_chunks": inserted,
                "error": None,
            },
            "$unset": {"_extracted_pages": ""},  # intermediate data no longer needed
        },
    )
    logger.info("Processed doc=%s chunks=%d", document_id, inserted)
    return {"document_id": document_id, "chunks": inserted, "status": "processed"}
