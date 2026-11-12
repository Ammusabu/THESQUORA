from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING

from app.database.collections import MESSAGES
from app.database.mongo_client import get_db


def _serialize(m: dict) -> dict:
    out = dict(m)
    out["id"] = str(out.pop("_id"))
    out["conversation_id"] = str(out["conversation_id"])
    out["user_id"] = str(out["user_id"])
    refs = []
    for r in out.get("source_references") or []:
        ref = dict(r)
        ref["document_id"] = str(ref["document_id"])
        refs.append(ref)
    out["source_references"] = refs
    out["feedback"] = m.get("feedback")
    return out


def add_message(
    *,
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    source_references: list[dict] | None = None,
) -> dict:
    doc = {
        "conversation_id": ObjectId(conversation_id),
        "user_id": ObjectId(user_id),
        "role": role,
        "content": content,
        "source_references": [
            {
                "document_id": ObjectId(r["document_id"]),
                "title": r["title"],
                "page_number": r.get("page_number"),
                "chunk_index": r.get("chunk_index"),
                "snippet": r.get("snippet"),
            }
            for r in (source_references or [])
        ],
        "created_at": datetime.now(timezone.utc),
    }
    res = get_db()[MESSAGES].insert_one(doc)
    doc["_id"] = res.inserted_id
    return _serialize(doc)


def list_for_conversation(conversation_id: str, *, limit: int = 200) -> list[dict]:
    cursor = (
        get_db()[MESSAGES]
        .find({"conversation_id": ObjectId(conversation_id)})
        .sort("created_at", ASCENDING)
        .limit(limit)
    )
    return [_serialize(m) for m in cursor]


def delete_for_conversation(conversation_id: str) -> int:
    return get_db()[MESSAGES].delete_many(
        {"conversation_id": ObjectId(conversation_id)}
    ).deleted_count


def set_feedback(message_id: str, *, user_id: str, rating: str | None) -> bool:
    """
    Persist thumbs up/down on an assistant message.
    Only the message owner can rate. `rating=None` clears the feedback.
    """
    from pymongo.errors import PyMongoError
    try:
        res = get_db()[MESSAGES].update_one(
            {"_id": ObjectId(message_id), "user_id": ObjectId(user_id)},
            {"$set": {"feedback": rating}},
        )
        return res.matched_count == 1
    except PyMongoError:
        return False
