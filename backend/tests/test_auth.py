from app.core.security import create_access_token, hash_password, verify_password


def test_hash_roundtrip():
    digest = hash_password("secret123")
    assert digest.startswith("pbkdf2$")
    assert verify_password("secret123", digest)
    assert not verify_password("wrong", digest)


def test_create_access_token_encodes_claims():
    token = create_access_token(subject="admin", role="admin")

    import jwt

    payload = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False})
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/api/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_admin_token(client, admin_headers):
    resp = client.get("/api/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"