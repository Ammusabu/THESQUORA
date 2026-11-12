from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.middleware.auth_middleware import get_current_user
from app.schemas.chat import (
    AskRequest, AskResponse, ConversationDetailResponse, ConversationListResponse,
)
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=AskResponse)
def ask(payload: AskRequest, current_user: dict = Depends(get_current_user)):
    return chat_service.ask(
        current_user=current_user,
        question=payload.question,
        conversation_id=payload.conversation_id,
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return chat_service.list_conversations(
        current_user=current_user, page=page, limit=limit,
    )


@router.get("/conversations/{conversation_id}",
            response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user),
):
    return chat_service.get_conversation(
        current_user=current_user, conversation_id=conversation_id,
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user),
):
    return chat_service.delete_conversation(
        current_user=current_user, conversation_id=conversation_id,
    )


class FeedbackBody(BaseModel):
    rating: str | None = None  # "up" | "down" | null


@router.post("/messages/{message_id}/feedback")
def feedback(
    message_id: str,
    body: FeedbackBody,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.set_message_feedback(
        current_user=current_user,
        message_id=message_id,
        rating=body.rating,
    )
