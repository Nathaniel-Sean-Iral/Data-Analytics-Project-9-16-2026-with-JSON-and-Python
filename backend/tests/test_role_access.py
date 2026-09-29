def test_viewer_cannot_create_household(client, viewer_headers):
    payload = {
        "household_no": "H-ROLE-001",
        "head_name": "Viewer Blocked",
        "address": "123 Blocked St",
        "barangay": "Poblacion",
        "size": 2,
        "children_count": 0,
        "elderly_count": 0,
        "pwd_count": 0,
        "contact": "09100000000",
        "lat": 14.9574,
        "lng": 120.9634,
    }

    response = client.post("/api/households", json=payload, headers=viewer_headers)

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_admin_can_create_household(client, admin_headers):
    payload = {
        "household_no": "H-ROLE-ADMIN-001",
        "head_name": "Admin Allowed",
        "address": "123 Allowed St",
        "barangay": "Poblacion",
        "size": 3,
        "children_count": 1,
        "elderly_count": 0,
        "pwd_count": 0,
        "contact": "09111111111",
        "lat": 14.9574,
        "lng": 120.9634,
    }

    response = client.post("/api/households", json=payload, headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["head_name"] == "Admin Allowed"


def test_responder_cannot_delete_household(client, responder_headers):
    response = client.delete("/api/households/1", headers=responder_headers)
    assert response.status_code == 403


def test_requester_without_token_is_rejected(client):
    response = client.get("/api/households")
    assert response.status_code == 401


def test_garbage_token_is_rejected(client):
    response = client.get("/api/households", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
