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


def test_dashboard_counts_distinct_assigned_households(client, admin_headers):
    """Regression: re-running the allocator inflated `assigned_households`.

    Allocation rows are retained for audit, so the same household reappears in
    every request. The dashboard must count distinct households, not rows.
    """
    payload = {"barangay": None}
    client.post("/api/evacuations/allocate", json=payload, headers=admin_headers)
    first = client.get("/api/dashboard/stats", headers=admin_headers).json()["assigned_households"]
    assert first == 6

    client.post("/api/evacuations/allocate", json=payload, headers=admin_headers)
    client.post("/api/evacuations/allocate", json=payload, headers=admin_headers)
    third = client.get("/api/dashboard/stats", headers=admin_headers).json()["assigned_households"]
    assert third == first