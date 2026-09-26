def test_meta_barangays(client, viewer_headers):
    resp = client.get("/api/meta/barangays", headers=viewer_headers)
    assert resp.status_code == 200
    assert "Poblacion" in resp.json()
    assert len(resp.json()) >= 8