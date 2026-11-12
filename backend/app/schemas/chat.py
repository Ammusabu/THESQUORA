from datetime import datetime
from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    document_id: str
    title: str
    page_number: int | None = None
    chunk_index: int | None = None
    snippet: str | None = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    source_references: list[SourceRef] = []
    created_at: datetime


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None


class AskResponse(BaseModel):
    conversation_id: str
    message: MessageOut
    context_used: int
    model: str | None = None
    usage: dict | None = None


class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationOut]
    total: int
    page: int
    limit: int


class ConversationDetailResponse(BaseModel):
    conversation: ConversationOut
    messages: list[MessageOut]
