"""
Pytest fixtures.

Design:
- `client` is a FastAPI TestClient bound to the real app.
- `test_user` registers a unique user per test run (uuid-based email) so
  tests are idempotent and can run repeatedly against the same Atlas db
  without collision.
- `auth_headers` logs in and returns {"Authorization": "Bearer ..."}.
- Cleanup deletes test users and their documents at session end.

NOTE: These tests hit the real Atlas database (integration tests, not unit
tests). For CI you'd point MONGO_URI at a dedicated test DB via env var.
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402
from app.database.collections import USERS, DOCUMENTS, CHUNKS  # noqa: E402
from app.database.mongo_client import get_db  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def test_user(client):
    """Register a unique test user and return (user_json, email, password)."""
    email = f"pytest-{uuid.uuid4().hex[:8]}@thesqora.local"
    password = "PytestPass123"
    r = client.post("/api/auth/register", json={
        "name": "Pytest User",
        "email": email,
        "password": password,
        "department": "QA",
    })
    assert r.status_code == 201, r.text
    user = r.json()

    yield {"user": user, "email": email, "password": password}

    # Teardown: delete this user's documents, chunks, and the user.
    db = get_db()
    from bson import ObjectId
    uid = ObjectId(user["id"])
    doc_ids = [d["_id"] for d in db[DOCUMENTS].find({"owner_id": uid}, {"_id": 1})]
    if doc_ids:
        db[CHUNKS].delete_many({"document_id": {"$in": doc_ids}})
    db[DOCUMENTS].delete_many({"owner_id": uid})
    db[USERS].delete_one({"_id": uid})


@pytest.fixture(scope="session")
def auth_headers(client, test_user):
    r = client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"],
    })
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_txt():
    return (
        "The API uses JWT bearer tokens for authentication. "
        "Deploy the backend with environment variables. "
        "Rate limiting protects login endpoints."
    ).encode("utf-8")
