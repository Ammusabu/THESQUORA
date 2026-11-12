"""Document endpoints."""
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.middleware.auth_middleware import get_current_user
from app.schemas.document import DocumentListResponse, DocumentOut
from app.services import document_service, similarity_service
from app.services import processing_service
from app.repositories import chunk_repository
from app.schemas.document_intel import (ClustersResponse, SimilarResponse)
from app.ml.clustering import run_clustering

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    department: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
):
    return await document_service.upload_document(
        file=file,
        current_user=current_user,
        title=title,
        department=department,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: str | None = Query(None),
    department: str | None = Query(None),
    q: str | None = Query(None, description="Keyword search"),
    current_user: dict = Depends(get_current_user),
):
    return document_service.list_my_documents(
        current_user=current_user,
        page=page, limit=limit,
        category=category, department=department, q=q,
    )


@router.get("/cluster/all", response_model=ClustersResponse)
def clusters(current_user: dict = Depends(get_current_user)):
    return run_clustering(current_user=current_user)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_one(doc_id: str, current_user: dict = Depends(get_current_user)):
    return document_service.get_document(doc_id, current_user=current_user)


@router.delete("/{doc_id}")
def delete(doc_id: str, current_user: dict = Depends(get_current_user)):
    return document_service.delete_document(doc_id, current_user=current_user)


@router.get("/{doc_id}/similar", response_model=SimilarResponse)
def similar_docs(
    doc_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    return similarity_service.similar_documents(
        document_id=doc_id, current_user=current_user, limit=limit,
    )


@router.get("/{doc_id}/preview")
def preview_document(
    doc_id: str,
    chunks: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    """Metadata + first N chunks — used by the preview drawer and compare modal."""
    doc = document_service.get_document(doc_id, current_user=current_user)
    chunk_docs = chunk_repository.list_for_document(doc_id, limit=chunks)
    return {
        "document": doc,
        "chunks": [
            {
                "chunk_index": c["chunk_index"],
                "page_number": c.get("page_number"),
                "text": c["text"],
            }
            for c in chunk_docs
        ],
    }


@router.post("/{doc_id}/reprocess")
def reprocess_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Re-run chunking + embedding for a document (idempotent)."""
    # ownership check (admin bypasses)
    document_service.get_document(doc_id, current_user=current_user)
    result = processing_service.process_document(doc_id)
    return result
