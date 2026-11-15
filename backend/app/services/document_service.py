"""
Document upload + retrieval business logic.

Upload flow:
  validate -> dedupe -> save file -> extract text -> insert metadata
Any failure after the file is saved attempts a best-effort cleanup.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, UploadFile, status
from pymongo.errors import DuplicateKeyError

from app.repositories import document_repository as repo
from app.services import storage_service
from app.utils.file_utils import read_and_validate
from app.utils.text_extraction import extract_text
from app.ml.classifier import predict as classify_text
from app.services.processing_service import process_document

logger = logging.getLogger(__name__)


async def upload_document(
    *,
    file: UploadFile,
    current_user: dict,
    title: str | None = None,
    department: str | None = None,
) -> dict[str, Any]:
    raw, ext, file_hash = await read_and_validate(file)

    # Per-user dedupe: the SAME file cannot exist twice in THIS user's
    # library, but other users can upload the same bytes independently.
    # Both this pre-check (friendly 409 before disk write) and the DB
    # compound-unique index (concurrency safety) are scoped to the owner.
    if repo.find_by_hash(file_hash, owner_id=current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already uploaded this document",
        )

    # Extract text BEFORE storing metadata so we can fail fast on bad files
    pages = extract_text(raw, ext)
    joined = "\n".join(pages)
    if len(joined.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Document has almost no readable text",
        )

    storage_key = storage_service.make_key(file_hash, ext)
    storage_service.save(storage_key, raw)

    doc = {
        "title": title or file.filename or "Untitled",
        "filename": file.filename or "unknown",
        "file_type": ext,
        "storage_key": storage_key,
        "file_hash": file_hash,
        "owner_id": ObjectId(current_user["id"]),
        "department": department or current_user.get("department"),
        "category": None,
        "classification_confidence": None,
        "upload_date": datetime.now(timezone.utc),
        "processing_status": "pending",
        "total_chunks": 0,
        "file_size": len(raw),
        "summary": None,
        "error": None,
    }
    try:
        created = repo.insert_document(doc)
    except DuplicateKeyError:
        # Lost a concurrent race — another upload of the same file by the
        # same owner won first. Clean up the orphaned storage and 409.
        storage_service.delete(storage_key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already uploaded this document",
        )

    try:
        repo.save_extracted_pages(created["id"], pages)
        repo.update_processing(created["id"], status="processing")
        category, confidence = classify_text(joined)
        repo.set_category(created["id"], category, confidence)
        #process_document(created["id"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("Post-insert processing failed: %s", exc)
        repo.update_processing(created["id"], status="failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Document stored but post-processing failed",
        ) from exc

    logger.info(
        "Uploaded doc id=%s owner=%s size=%d hash=%s pages=%d",
        created["id"], current_user["id"], len(raw), file_hash[:8], len(pages),
    )
    return repo.find_by_id(created["id"])  # type: ignore[return-value]


def list_my_documents(
    *,
    current_user: dict,
    page: int,
    limit: int,
    category: str | None,
    department: str | None,
    q: str | None,
) -> dict[str, Any]:
    items, total = repo.list_documents(
        user_id=current_user["id"],
        role=current_user["role"],
        page=page,
        limit=limit,
        category=category,
        department=department,
        q=q,
    )
    return {"items": items, "total": total, "page": page, "limit": limit}


def _assert_access(doc: dict | None, current_user: dict) -> dict:
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user["role"] != "admin" and str(doc["owner_id"]) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorised for this document")
    return doc


def get_document(doc_id: str, *, current_user: dict) -> dict:
    doc = repo.find_by_id(doc_id)
    return _assert_access(doc, current_user)


def delete_document(doc_id: str, *, current_user: dict) -> dict:
    """
    Delete a document and remove its chunks.

    Storage safety: multiple users can share the same physical file (same
    `storage_key`). We only remove the file from disk when NO other
    document row references it after this deletion.
    """
    doc = _assert_access(repo.find_by_id(doc_id), current_user)
    storage_key = doc.get("storage_key", "")

    # 1. Delete the DB row + cascade chunks
    repo.delete_by_id(doc_id)
    from app.repositories import chunk_repository as chunks_repo
    chunks_repo.delete_for_document(doc_id)

    # 2. Only remove the physical file if the last reference is gone
    if storage_key:
        from app.database.collections import DOCUMENTS
        from app.database.mongo_client import get_db
        remaining = get_db()[DOCUMENTS].count_documents({"storage_key": storage_key})
        if remaining == 0:
            storage_service.delete(storage_key)

    logger.info("Deleted document %s by %s", doc_id, current_user["id"])
    return {"deleted": True, "id": doc_id}
