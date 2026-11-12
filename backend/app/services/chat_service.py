"""
Chat orchestration:
  ask(): optionally create a conversation, save user message, retrieve,
         call LLM, save assistant message + sources, touch updated_at.
  list()/get()/delete() are thin RBAC wrappers.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

from app.rag import answer_generator
from app.repositories import conversation_repository as conv_repo
from app.repositories import message_repository as msg_repo

logger = logging.getLogger(__name__)


def ask(
    *,
    current_user: dict,
    question: str,
    conversation_id: str | None,
) -> dict[str, Any]:
    question = (question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 1. Resolve or create conversation
    if conversation_id:
        conv = conv_repo.find_by_id(
            conversation_id,
            user_id=current_user["id"],
            is_admin=current_user["role"] == "admin",
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = conv_repo.create(user_id=current_user["id"], title="New conversation")

    cid = conv["id"]

    # 2. Persist user turn
    msg_repo.add_message(
        conversation_id=cid,
        user_id=current_user["id"],
        role="user",
        content=question,
    )

    # 3. Build history for the prompt (last turns)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in msg_repo.list_for_conversation(cid, limit=20)
        if m["role"] in ("user", "assistant")
    ]

    # 4. Generate grounded answer
    try:
        result = answer_generator.generate_answer(
            current_user=current_user,
            question=question,
            history=history[:-1],  # exclude the just-saved user message
            top_k=5,               # reranker now handles precision
        )
    except RuntimeError as exc:
        logger.error("Answer generation failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM unavailable, try again") from exc

    # 5. Persist assistant turn with citations
    saved = msg_repo.add_message(
        conversation_id=cid,
        user_id=current_user["id"],
        role="assistant",
        content=result["answer"],
        source_references=[
            {
                "document_id": s["document_id"],
                "title": s["title"],
                "page_number": s.get("page_number"),
                "chunk_index": s.get("chunk_index"),
                "snippet": s.get("snippet"),
            }
            for s in result["sources"]
        ],
    )

    # 6. Housekeeping
    conv_repo.add_title_if_placeholder(cid, question)
    conv_repo.touch(cid)

    return {
        "conversation_id": cid,
        "message": saved,
        "context_used": result["context_used"],
        "model": result["model"],
        "usage": result["usage"],
    }


def list_conversations(*, current_user: dict, page: int, limit: int) -> dict:
    items, total = conv_repo.list_for_user(
        user_id=current_user["id"], page=page, limit=limit,
    )
    return {"items": items, "total": total, "page": page, "limit": limit}


def get_conversation(*, current_user: dict, conversation_id: str) -> dict:
    conv = conv_repo.find_by_id(
        conversation_id,
        user_id=current_user["id"],
        is_admin=current_user["role"] == "admin",
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = msg_repo.list_for_conversation(conversation_id)
    return {"conversation": conv, "messages": messages}


def delete_conversation(*, current_user: dict, conversation_id: str) -> dict:
    ok = conv_repo.delete(
        conversation_id,
        user_id=current_user["id"],
        is_admin=current_user["role"] == "admin",
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg_repo.delete_for_conversation(conversation_id)
    return {"deleted": True, "id": conversation_id}


def set_message_feedback(
    *, current_user: dict, message_id: str, rating: str | None,
) -> dict:
    if rating not in ("up", "down", None):
        raise HTTPException(status_code=400, detail="Invalid rating")
    ok = msg_repo.set_feedback(message_id, user_id=current_user["id"], rating=rating)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"ok": True, "rating": rating}
