def test_list_resources(client, viewer_headers):
    resp = client.get("/api/resources", headers=viewer_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_resource_summary(client, viewer_headers):
    resp = client.get("/api/resources/summary", headers=viewer_headers)
    assert resp.status_code == 200
    summaries = {s["type"]: s for s in resp.json()}
    assert summaries["rice"]["total_on_hand"] == 100
    assert summaries["rice"]["total_required"] == 150
    assert summaries["rice"]["gap"] == -50
    assert summaries["rice"]["low_stock_count"] == 1


def test_adjust_stock(client, admin_headers):
    resp = client.post(
        "/api/resources/adjust",
        json={"resource_id": 1, "delta": 25, "reason": "restock"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["quantity_on_hand"] == 125


def test_adjust_stock_negative_blocked(client, admin_headers):
    resp = client.post(
        "/api/resources/adjust",
        json={"resource_id": 2, "delta": -999},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_update_threshold_via_patch(client, admin_headers):
    resp = client.patch("/api/resources/1", json={"threshold": 90}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["threshold"] == 90


def test_adjust_forbidden_for_viewer(client, viewer_headers):
    resp = client.post(
        "/api/resources/adjust",
        json={"resource_id": 1, "delta": 10},
        headers=viewer_headers,
    )
    assert resp.status_code == 403