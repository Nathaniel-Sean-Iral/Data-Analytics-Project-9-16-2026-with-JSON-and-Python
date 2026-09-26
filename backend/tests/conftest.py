import os
import tempfile

# Point the app at a throwaway SQLite file BEFORE importing app modules.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.center import EvacuationCenter  # noqa: E402
from app.models.household import Household  # noqa: E402
from app.models.incident import Incident  # noqa: E402
from app.models.resource import Resource  # noqa: E402
from app.models.user import User  # noqa: E402

TEST_ENGINE = create_engine(f"sqlite:///{_tmp_db.name}", connect_args={"check_same_thread": False})
TEST_SESSION = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)

PASSWORDS = {"admin": "admin", "responder": "responder", "viewer": "viewer"}


def override_get_db():
    db = TEST_SESSION()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def _seed():
    db = TEST_SESSION()
    try:
        for username, password in PASSWORDS.items():
            db.add(
                User(
                    username=username,
                    full_name=username.capitalize(),
                    email=f"{username}@test.local",
                    role=username,
                    hashed_password=hash_password(password),
                    is_active=True,
                )
            )
        barangays = ["Poblacion", "San Roque", "Malanday", "San Juan", "Kalayaan", "San Roque"]
        for i in range(6):
            db.add(
                Household(
                    household_no=f"HH-{i + 1:04d}",
                    head_name=f"Head {i}",
                    address=f"Blk {i + 1}, Brgy",
                    barangay=barangays[i],
                    size=4,
                    children_count=2,
                    elderly_count=1,
                    pwd_count=0,
                    contact=f"09{i:08d}",
                    lat=14.08 + i * 0.02,
                    lng=121.14 + i * 0.018,
                )
            )
        db.add(
            EvacuationCenter(
                name="Test Center A",
                barangay="Poblacion",
                address="Brgy Hall Rd",
                capacity=50,
                current_occupants=10,
                facilities=["kitchen", "water"],
                contact="09171234001",
                lat=14.095,
                lng=121.148,
                status="active",
            )
        )
        db.add(
            EvacuationCenter(
                name="Test Center B",
                barangay="San Roque",
                address="Mabini St",
                capacity=20,
                current_occupants=15,
                facilities=["water"],
                contact="09171234002",
                lat=14.082,
                lng=121.13,
                status="active",
            )
        )
        db.add(
            Resource(
                name="Rice (50kg sack)",
                type="rice",
                unit="sacks",
                quantity_on_hand=100,
                threshold=150,
                stored_in="Warehouse",
            )
        )
        db.add(
            Resource(
                name="Tents",
                type="tents",
                unit="pc",
                quantity_on_hand=12,
                threshold=30,
                stored_in="MDRRMO",
            )
        )
        db.add(Incident(title="Flood", type="flood", barangay="Malanday", severity="high", status="assessing"))
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client():
    """Fresh in-memory DB per test so tests never leak state into each other."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    _seed()
    with TestClient(app) as c:
        yield c


def login(client, username: str):
    resp = client.post("/api/auth/login", json={"username": username, "password": PASSWORDS[username]})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return login(client, "admin")


@pytest.fixture()
def responder_headers(client):
    return login(client, "responder")


@pytest.fixture()
def viewer_headers(client):
    return login(client, "viewer")