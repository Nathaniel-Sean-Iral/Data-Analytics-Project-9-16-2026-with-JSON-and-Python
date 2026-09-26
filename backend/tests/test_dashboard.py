def test_dashboard_stats(client, viewer_headers):
    resp = client.get("/api/dashboard/stats", headers=viewer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["households"] == 6
    assert body["vulnerable_members"] == 18  # 6 * (2 children + 1 elderly + 0 pwd)
    assert body["active_incidents"] == 1
    assert body["critical_incidents"] == 0
    assert body["centers"] == 2
    assert body["available_capacity"] == (50 - 10) + (20 - 15)  # 40 + 5
    assert body["low_stock_resources"] == 2  # both below threshold
    assert body["assigned_households"] == 0


def test_dashboard_requires_auth(client):
    assert client.get("/api/dashboard/stats").status_code == 401