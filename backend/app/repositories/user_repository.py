"""
PyMongo access layer for the `users` collection.

Design notes:
- Never expose password_hash to callers: use `projection` to strip it in
  read methods that return to the API.
- Unique index on `email` prevents duplicates at the DB level; we still
  catch DuplicateKeyError for a clean 409 response.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.database.collections import USERS
from app.database.mongo_client import get_db

# Projection used everywhere we read a user for the API layer.
SAFE_PROJECTION = {"password_hash": 0}


def _serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def create_user(
    *,
    name: str,
    email: str,
    password_hash: str,
    role: str = "user",
    department: str | None = None,
) -> dict[str, Any]:
    """Insert a new user. Raises DuplicateKeyError if email exists."""
    db = get_db()
    doc = {
        "name": name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "role": role,
        "department": department,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = db[USERS].insert_one(doc)
    except DuplicateKeyError:
        raise
    doc["_id"] = result.inserted_id
    return _serialize(doc)  # type: ignore[return-value]


def find_by_email(email: str, *, with_password: bool = False) -> dict[str, Any] | None:
    db = get_db()
    projection = None if with_password else SAFE_PROJECTION
    doc = db[USERS].find_one({"email": email.lower().strip()}, projection)
    return _serialize(doc)


def find_by_id(user_id: str, *, with_password: bool = False) -> dict[str, Any] | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    db = get_db()
    projection = None if with_password else SAFE_PROJECTION
    doc = db[USERS].find_one({"_id": oid}, projection)
    return _serialize(doc)


def count_users() -> int:
    return get_db()[USERS].count_documents({})
