def test_list_centers(client, viewer_headers):
    resp = client.get("/api/centers", headers=viewer_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_centers_filter_by_status(client, viewer_headers):
    resp = client.get("/api/centers?status=standby", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_center(client, viewer_headers):
    resp = client.get("/api/centers/1", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Center A"


def test_get_center_not_found(client, viewer_headers):
    assert client.get("/api/centers/9999", headers=viewer_headers).status_code == 404


def test_create_center_admin_only(client, admin_headers, viewer_headers):
    payload = {
        "name": "New Gym",
        "barangay": "Kalayaan",
        "address": "Road 1",
        "capacity": 200,
        "current_occupants": 0,
        "facilities": ["water"],
    }
    assert client.get("/api/centers/99999", headers=viewer_headers).status_code == 404  # noqa: S101
    resp = client.post("/api/centers", json=payload, headers=viewer_headers)
    assert resp.status_code == 403
    resp = client.post("/api/centers", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "New Gym"


def test_update_center(client, admin_headers):
    resp = client.put("/api/centers/1", json={"capacity": 120}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 120


def test_delete_center(client, admin_headers):
    resp = client.delete("/api/centers/2", headers=admin_headers)
    assert resp.status_code == 204
    assert client.get("/api/centers/2", headers=admin_headers).status_code == 404