"""Pydantic schemas for documents."""
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    owner_id: str
    department: str | None = None
    category: str | None = None
    classification_confidence: float | None = None
    upload_date: datetime
    processing_status: str
    total_chunks: int = 0
    file_size: int = 0
    summary: str | None = None
    error: str | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int
    page: int
    limit: int


class DocumentListQuery(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    category: str | None = None
    department: str | None = None
    q: str | None = None
