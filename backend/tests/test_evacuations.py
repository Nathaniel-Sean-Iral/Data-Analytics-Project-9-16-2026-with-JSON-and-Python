def test_allocate(client, responder_headers):
    resp = client.post("/api/evacuations/allocate", json={}, headers=responder_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_id"].startswith("ALLOC-")
    assert body["total_households"] == 6
    assert body["assigned_households"] >= 1
    assert body["center_loads"]

    loads = {l["center_id"]: l for l in body["center_loads"]}
    # Test Center A (capacity 50, 10 occupied) absorbs the most.
    assert loads[1]["load_percent"] < loads[2]["load_percent"]


def test_allocate_filtered_by_barangay(client, responder_headers):
    resp = client.post(
        "/api/evacuations/allocate",
        json={"barangay": "San Roque"},
        headers=responder_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_households"] == 2
    for a in body["assignments"]:
        assert a["barangay"] == "San Roque"


def test_center_loads(client, viewer_headers):
    resp = client.get("/api/evacuations/center-loads", headers=viewer_headers)
    assert resp.status_code == 200
    loads = {l["center_id"]: l for l in resp.json()}
    assert loads[1]["occupants"] == 10
    assert loads[2]["load_percent"] == 75  # 15/20


def test_allocate_denied_for_viewer(client, viewer_headers):
    assert client.post("/api/evacuations/allocate", json={}, headers=viewer_headers).status_code == 403