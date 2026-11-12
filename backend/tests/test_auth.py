import uuid


def test_register_first_user_is_admin_or_user(client):
    email = f"auth-{uuid.uuid4().hex[:8]}@thesqora.local"
    r = client.post("/api/auth/register", json={
        "name": "Auth Tester", "email": email, "password": "AuthPass123",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == email
    assert body["role"] in ("admin", "user")
    assert "password_hash" not in body
    assert "id" in body


def test_register_duplicate_email_returns_409(client, test_user):
    r = client.post("/api/auth/register", json={
        "name": "Dup", "email": test_user["email"], "password": "Whatever123",
    })
    assert r.status_code == 409


def test_login_wrong_password_returns_401(client, test_user):
    r = client.post("/api/auth/login", json={
        "email": test_user["email"], "password": "wrong",
    })
    assert r.status_code == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_profile(client, auth_headers, test_user):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == test_user["email"]
    assert "password_hash" not in body
