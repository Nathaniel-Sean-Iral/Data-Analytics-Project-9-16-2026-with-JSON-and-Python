from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.household import Household


def test_household_create_persists_to_database():
    db = SessionLocal()
    db.query(Household).delete()
    db.commit()
    db.close()

    client = TestClient(app)
    payload = {
        "household_no": "H-TEST-001",
        "head_name": "Test Household",
        "address": "123 Test Street",
        "barangay": "Barangay 1",
        "size": 4,
        "children_count": 1,
        "elderly_count": 1,
        "pwd_count": 0,
        "contact": "09999999999",
        "lat": 14.6000,
        "lng": 120.9800,
        "notes": "Created by test",
    }

    response = client.post("/api/households", json=payload)
    assert response.status_code == 200, response.text

    db = SessionLocal()
    count = db.query(Household).count()
    db.close()
    assert count == 1
