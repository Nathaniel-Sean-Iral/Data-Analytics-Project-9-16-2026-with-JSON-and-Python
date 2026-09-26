def test_list_households(client, viewer_headers):
    resp = client.get("/api/households", headers=viewer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 6
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 6


def test_households_pagination(client, viewer_headers):
    resp = client.get("/api/households?page=2&page_size=5", headers=viewer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["total"] == 6
    assert len(body["items"]) == 1


def test_households_search(client, viewer_headers):
    resp = client.get("/api/households?q=Head 3", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_households_filter_by_barangay(client, viewer_headers):
    resp = client.get("/api/households?barangay=San Roque", headers=viewer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2


def test_get_household_not_found(client, viewer_headers):
    assert client.get("/api/households/9999", headers=viewer_headers).status_code == 404


def test_create_household_as_admin(client, admin_headers):
    payload = {
        "household_no": "HH-9899",
        "head_name": "New Head",
        "address": "Blk 9",
        "barangay": "Poblacion",
        "size": 3,
    }
    resp = client.post("/api/households", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["household_no"] == "HH-9899"


def test_create_household_duplicate_409(client, admin_headers):
    payload = {
        "household_no": "HH-0001",
        "head_name": "Dup",
        "address": "Blk 1",
        "barangay": "Poblacion",
        "size": 2,
    }
    assert client.post("/api/households", json=payload, headers=admin_headers).status_code == 409


def test_create_household_forbidden_for_viewer(client, viewer_headers):
    payload = {
        "household_no": "HH-8888",
        "head_name": "Nope",
        "address": "Blk 9",
        "barangay": "Poblacion",
        "size": 2,
    }
    assert client.post("/api/households", json=payload, headers=viewer_headers).status_code == 403


def test_update_household(client, admin_headers):
    resp = client.put("/api/households/1", json={"head_name": "Renamed"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["head_name"] == "Renamed"


def test_delete_household(client, admin_headers):
    resp = client.delete("/api/households/6", headers=admin_headers)
    assert resp.status_code == 204