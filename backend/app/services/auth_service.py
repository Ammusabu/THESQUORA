"""Business logic for registration, login, and current-user lookup."""
import logging
from datetime import datetime

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.repositories import user_repository as repo
from app.utils.security import (
    create_access_token, hash_password, verify_password,
)

logger = logging.getLogger(__name__)


def register(
    *, name: str, email: str, password: str, department: str | None,
) -> dict:
    # First user becomes admin (so you can bootstrap without manual DB seeding).
    is_first = repo.count_users() == 0
    role = "admin" if is_first else "user"

    try:
        user = repo.create_user(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            department=department,
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    logger.info("Registered user %s (role=%s)", user["email"], role)
    return user


def login(*, email: str, password: str) -> dict:
    # Fetch WITH password for verification, but return WITHOUT it.
    raw = repo.find_by_email(email, with_password=True)
    if not raw or not verify_password(password, raw.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=raw["id"], role=raw["role"])
    safe_user = repo.find_by_id(raw["id"])  # projected, no password_hash
    logger.info("User %s logged in", raw["email"])
    return {"access_token": token, "token_type": "bearer", "user": safe_user}


def get_me(user_id: str) -> dict:
    user = repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
