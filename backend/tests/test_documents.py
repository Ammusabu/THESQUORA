import io


def _upload(client, headers, content: bytes, name="doc.txt", **extra):
    """
    Multipart upload helper.
    `files` carries the file part only. `data` carries form fields (title,
    department). Mixing them sends 'title' as a file part, which FastAPI
    rejects with 'body.title must be string'.
    """
    files = {"file": (name, io.BytesIO(content), "text/plain")}
    form: dict = {}
    if "title" in extra:
        form["title"] = extra["title"]
    if "department" in extra:
        form["department"] = extra["department"]
    return client.post("/api/documents/upload", headers=headers,
                       files=files, data=form)


def test_upload_creates_document_with_chunks(client, auth_headers, sample_txt):
    r = _upload(client, auth_headers, sample_txt,
                title="Auth Test Doc", department="QA")
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["title"] == "Auth Test Doc"
    assert d["file_type"] == "txt"
    assert d["processing_status"] == "processed"
    assert d["total_chunks"] >= 1
    assert d["category"] is not None
    assert d["classification_confidence"] is not None


def test_duplicate_upload_returns_409(client, auth_headers, sample_txt):
    _upload(client, auth_headers, sample_txt)
    r = _upload(client, auth_headers, sample_txt)
    assert r.status_code == 409


def test_bad_extension_rejected(client, auth_headers):
    r = _upload(client, auth_headers, b"fake", name="bad.exe")
    assert r.status_code == 400


def test_empty_file_rejected(client, auth_headers):
    r = _upload(client, auth_headers, b"")
    assert r.status_code == 400


def test_list_documents_pagination(client, auth_headers):
    r = client.get("/api/documents?page=1&limit=2", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    assert body["page"] == 1
    assert body["limit"] == 2


def test_cross_user_access_forbidden(client, auth_headers, sample_txt):
    import uuid

    # Unique content avoids 409 from an earlier run
    unique_content = sample_txt + f" unique-{uuid.uuid4().hex}".encode()

    r = _upload(client, auth_headers, unique_content,
                title=f"Cross Test {uuid.uuid4().hex[:6]}")
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]

    other_email = f"other-{uuid.uuid4().hex[:6]}@thesqora.local"
    client.post("/api/auth/register", json={
        "name": "Other", "email": other_email, "password": "OtherPass123",
    })
    other_token = client.post("/api/auth/login", json={
        "email": other_email, "password": "OtherPass123",
    }).json()["access_token"]

    r2 = client.get(f"/api/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {other_token}"})
    assert r2.status_code == 403


# ---------------------------------------------------------------------------
# Per-user duplicate detection (Phase 13.5)
# ---------------------------------------------------------------------------
def test_different_users_can_upload_same_file(client, auth_headers, sample_txt):
    """
    User A uploads a file -> succeeds.
    User B uploads the SAME bytes -> must also succeed (per-user dedupe).
    """
    import uuid

    # Fresh unique content so this test isn't affected by prior state
    content = sample_txt + f" userA-{uuid.uuid4().hex}".encode()

    r_a = _upload(client, auth_headers, content, title="Shared Doc (A)")
    assert r_a.status_code == 201, r_a.text

    # Second user
    email_b = f"userb-{uuid.uuid4().hex[:8]}@thesqora.local"
    client.post("/api/auth/register", json={
        "name": "User B", "email": email_b, "password": "UserBPass123",
    })
    token_b = client.post("/api/auth/login", json={
        "email": email_b, "password": "UserBPass123",
    }).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r_b = _upload(client, headers_b, content, title="Shared Doc (B)")
    assert r_b.status_code == 201, f"User B blocked from uploading identical file: {r_b.text}"

    # Both documents exist and have distinct owner_ids
    assert r_a.json()["id"] != r_b.json()["id"]
    assert r_a.json()["owner_id"] != r_b.json()["owner_id"]


def test_same_user_cannot_upload_identical_file_twice(client, auth_headers, sample_txt):
    """Same user tries to upload the same bytes twice -> 409."""
    import uuid

    content = sample_txt + f" dup-{uuid.uuid4().hex}".encode()

    r1 = _upload(client, auth_headers, content, title="Dup Test 1")
    assert r1.status_code == 201, r1.text

    r2 = _upload(client, auth_headers, content, title="Dup Test 2")
    assert r2.status_code == 409, r2.text
    assert "already uploaded" in r2.json()["detail"].lower()


def test_deleting_one_users_copy_does_not_break_other(client, auth_headers, sample_txt):
    """
    User A and User B both upload the same physical file (same storage_key).
    When User A deletes their copy, User B's copy must still be readable.
    """
    import uuid

    content = sample_txt + f" shared-{uuid.uuid4().hex}".encode()

    # User A uploads
    r_a = _upload(client, auth_headers, content, title="Shared (A)")
    assert r_a.status_code == 201, r_a.text
    doc_a = r_a.json()

    # User B uploads the same bytes
    email_b = f"userb-{uuid.uuid4().hex[:8]}@thesqora.local"
    client.post("/api/auth/register", json={
        "name": "User B", "email": email_b, "password": "UserBPass123",
    })
    token_b = client.post("/api/auth/login", json={
        "email": email_b, "password": "UserBPass123",
    }).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r_b = _upload(client, headers_b, content, title="Shared (B)")
    assert r_b.status_code == 201, r_b.text
    doc_b = r_b.json()

    # Both point to the same physical file
    from app.database.collections import DOCUMENTS
    from app.database.mongo_client import get_db
    from bson import ObjectId
    db = get_db()
    row_a = db[DOCUMENTS].find_one({"_id": ObjectId(doc_a["id"])})
    row_b = db[DOCUMENTS].find_one({"_id": ObjectId(doc_b["id"])})
    assert row_a["storage_key"] == row_b["storage_key"]

    # User A deletes their copy
    r_del = client.delete(f"/api/documents/{doc_a['id']}", headers=auth_headers)
    assert r_del.status_code == 200, r_del.text

    # User B can still fetch their copy
    r_b_get = client.get(f"/api/documents/{doc_b['id']}", headers=headers_b)
    assert r_b_get.status_code == 200, f"User B lost access: {r_b_get.text}"
