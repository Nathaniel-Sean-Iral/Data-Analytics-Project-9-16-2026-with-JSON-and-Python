import time

import jwt
import pytest

from app.core.config import INSECURE_PLACEHOLDER_SECRETS, Settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.services.store import authenticate_user


def test_password_hashing_round_trip():
    stored = hash_password("correct-horse-battery")
    assert stored != "correct-horse-battery"
    assert "correct-horse-battery" not in stored
    assert verify_password("correct-horse-battery", stored) is True
    assert verify_password("wrong-password", stored) is False
    assert verify_password("correct-horse-battery", None) is False
    assert verify_password("correct-horse-battery", "garbage") is False


def test_hashes_are_salted_so_identical_passwords_differ():
    assert hash_password("same-password-1") != hash_password("same-password-1")


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_needs_rehash_detects_weak_and_unknown_schemes():
    assert needs_rehash(None) is True
    assert needs_rehash("") is True
    assert needs_rehash("plaintext-password") is True
    assert needs_rehash("pbkdf2_sha256$1000$aa$bb") is True
    assert needs_rehash(hash_password("a-valid-password")) is False


def test_login_returns_tokens_and_user(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_login_never_returns_a_password_hash(client):
    body = client.post("/api/auth/login", json={"username": "admin", "password": "password"}).json()
    assert "password_hash" not in str(body)


def test_wrong_password_is_rejected(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert response.status_code == 401


def test_unknown_user_is_rejected(client):
    response = client.post("/api/auth/login", json={"username": "ghost", "password": "password"})
    assert response.status_code == 401


def test_oauth2_password_flow_issues_token_pair(client):
    response = client.post(
        "/api/auth/token",
        data={"username": "responder", "password": "password"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_access_token_is_a_signed_jwt(client):
    body = client.post("/api/auth/login", json={"username": "admin", "password": "password"}).json()
    claims = decode_token(body["access_token"], "access")
    assert claims["sub"] == "admin"
    assert claims["role"] == "admin"
    assert claims["type"] == "access"


def test_refresh_token_cannot_be_used_as_an_access_token(client):
    body = client.post("/api/auth/login", json={"username": "admin", "password": "password"}).json()
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(body["refresh_token"], "access")

    response = client.get("/api/households", headers={"Authorization": f"Bearer {body['refresh_token']}"})
    assert response.status_code == 401


def test_token_signed_with_another_secret_is_rejected(client):
    forged = jwt.encode(
        {"sub": "admin", "role": "admin", "type": "access", "exp": int(time.time()) + 600},
        "attacker-secret-key-that-is-long-enough-1234",
        algorithm="HS256",
    )
    response = client.get("/api/households", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_alg_none_token_is_rejected(client):
    forged = jwt.encode({"sub": "admin", "role": "admin", "type": "access"}, key="", algorithm="none")
    response = client.get("/api/households", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_expired_token_is_rejected(client):
    expired = jwt.encode(
        {"sub": "admin", "role": "admin", "type": "access", "exp": int(time.time()) - 60},
        "test-secret-key-not-a-placeholder-value-0123456789",
        algorithm="HS256",
    )
    response = client.get("/api/households", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_me_endpoint_returns_the_authenticated_user(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["username"] == "admin"
    assert response.json()["role"] == "admin"


def test_refresh_endpoint_issues_new_tokens(client):
    body = client.post("/api/auth/login", json={"username": "viewer", "password": "password"}).json()
    response = client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert response.status_code == 200, response.text
    refreshed = response.json()
    assert refreshed["access_token"]
    assert decode_token(refreshed["access_token"], "access")["sub"] == "viewer"


def test_refresh_rejects_a_garbage_token(client):
    response = client.post("/api/auth/refresh", json={"refresh_token": "nonsense"})
    assert response.status_code == 401


def test_stale_role_in_token_is_rejected(client):
    stale = create_access_token("admin", "viewer")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {stale}"})
    assert response.status_code == 401


def test_admin_can_register_a_user(client, admin_headers):
    response = client.post(
        "/api/auth/users",
        json={"username": "field.officer", "full_name": "Field Officer", "password": "a-strong-password", "role": "responder"},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["username"] == "field.officer"
    assert response.json()["role"] == "responder"

    login = client.post("/api/auth/login", json={"username": "field.officer", "password": "a-strong-password"})
    assert login.status_code == 200, login.text


def test_responder_cannot_register_a_user(client, responder_headers):
    response = client.post(
        "/api/auth/users",
        json={"username": "sneaky", "full_name": "Sneaky", "password": "a-strong-password"},
        headers=responder_headers,
    )
    assert response.status_code == 403


def test_duplicate_username_is_conflict(client, admin_headers):
    payload = {"username": "dupe", "full_name": "Dupe", "password": "a-strong-password"}
    assert client.post("/api/auth/users", json=payload, headers=admin_headers).status_code == 201
    second = client.post("/api/auth/users", json=payload, headers=admin_headers)
    assert second.status_code == 409


def test_weak_password_is_rejected_by_validation(client, admin_headers):
    response = client.post(
        "/api/auth/users",
        json={"username": "weakling", "full_name": "Weak", "password": "short"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_authenticate_user_returns_none_for_bad_credentials():
    assert authenticate_user("admin", "password") is not None
    assert authenticate_user("admin", "wrong") is None
    assert authenticate_user("nobody", "password") is None


def test_placeholder_secret_keys_are_refused():
    for placeholder in INSECURE_PLACEHOLDER_SECRETS:
        with pytest.raises(ValueError):
            Settings(SECRET_KEY=placeholder)


def test_production_requires_an_explicit_secret_key():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", _env_file=None)


def test_production_refuses_demo_seeding():
    with pytest.raises(ValueError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-real-looking-production-secret-key-9999",
            SEED_DEMO_DATA=True,
            _env_file=None,
        )


def test_development_gets_a_random_secret_without_configuration():
    configured = Settings(_env_file=None)
    other = Settings(SECRET_KEY="a-different-random-looking-secret-key-7777", _env_file=None)
    assert configured.SECRET_KEY != other.SECRET_KEY
    assert configured.SECRET_KEY not in INSECURE_PLACEHOLDER_SECRETS
