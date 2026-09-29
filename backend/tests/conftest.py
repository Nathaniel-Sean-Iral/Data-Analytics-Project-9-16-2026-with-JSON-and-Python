import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "disaster_prep_test.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-not-a-placeholder-value-0123456789"
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["DEMO_PASSWORD"] = "password"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.services.store import seed_demo_data

DEMO_PASSWORD = os.environ["DEMO_PASSWORD"]


@pytest.fixture(scope="session", autouse=True)
def prepared_database():
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if _TEST_DB.exists():
        _TEST_DB.unlink()


@pytest.fixture(scope="session")
def client(prepared_database):
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return _login(client, "admin")


@pytest.fixture
def responder_headers(client):
    return _login(client, "responder")


@pytest.fixture
def viewer_headers(client):
    return _login(client, "viewer")


@pytest.fixture
def anon_headers():
    return {}
