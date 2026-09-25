from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_viewer_cannot_create_household():
    payload = {
        "household_no": "H-ROLE-001",
        "head_name": "Viewer Blocked",
        "address": "123 Blocked St",
        "barangay": "Barangay 1",
        "size": 2,
        "children_count": 0,
        "elderly_count": 0,
        "pwd_count": 0,
        "contact": "09100000000",
        "lat": 14.6000,
        "lng": 120.9800,
    }

    response = client.post(
        "/api/households",
        json=payload,
        headers={"Authorization": "Bearer mock-token-viewer"},
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_admin_can_create_household():
    payload = {
        "household_no": "H-ROLE-ADMIN-001",
        "head_name": "Admin Allowed",
        "address": "123 Allowed St",
        "barangay": "Barangay 1",
        "size": 3,
        "children_count": 1,
        "elderly_count": 0,
        "pwd_count": 0,
        "contact": "09111111111",
        "lat": 14.6000,
        "lng": 120.9800,
    }

    response = client.post(
        "/api/households",
        json=payload,
        headers={"Authorization": "Bearer mock-token-admin"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["head_name"] == "Admin Allowed"
