from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING

from app.database.collections import CONVERSATIONS
from app.database.mongo_client import get_db


def _serialize(doc: dict | None) -> dict | None:
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    if "user_id" in out:
        out["user_id"] = str(out["user_id"])
    return out


def create(*, user_id: str, title: str) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user_id),
        "title": title[:200] or "New conversation",
        "created_at": now,
        "updated_at": now,
    }
    result = get_db()[CONVERSATIONS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)  # type: ignore[return-value]


def find_by_id(conv_id: str, *, user_id: str, is_admin: bool) -> dict | None:
    try:
        oid = ObjectId(conv_id)
    except Exception:
        return None
    q: dict = {"_id": oid}
    if not is_admin:
        q["user_id"] = ObjectId(user_id)
    return _serialize(get_db()[CONVERSATIONS].find_one(q))


def list_for_user(*, user_id: str, page: int, limit: int) -> tuple[list[dict], int]:
    q = {"user_id": ObjectId(user_id)}
    total = get_db()[CONVERSATIONS].count_documents(q)
    cursor = (
        get_db()[CONVERSATIONS]
        .find(q)
        .sort("updated_at", DESCENDING)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    return [_serialize(d) for d in cursor], total  # type: ignore[misc]


def touch(conv_id: str) -> None:
    get_db()[CONVERSATIONS].update_one(
        {"_id": ObjectId(conv_id)},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
    )


def delete(conv_id: str, *, user_id: str, is_admin: bool) -> bool:
    try:
        oid = ObjectId(conv_id)
    except Exception:
        return False
    q: dict = {"_id": oid}
    if not is_admin:
        q["user_id"] = ObjectId(user_id)
    res = get_db()[CONVERSATIONS].delete_one(q)
    return res.deleted_count == 1


def add_title_if_placeholder(conv_id: str, first_question: str) -> None:
    """If title is the default, derive one from the first question."""
    try:
        oid = ObjectId(conv_id)
    except Exception:
        return
    conv = get_db()[CONVERSATIONS].find_one({"_id": oid}, {"title": 1})
    if not conv:
        return
    if conv["title"] in ("New conversation", ""):
        new_title = first_question.strip()[:100] or "New conversation"
        get_db()[CONVERSATIONS].update_one(
            {"_id": oid}, {"$set": {"title": new_title}}
        )
