def test_list_incidents(client, viewer_headers):
    resp = client.get("/api/incidents", headers=viewer_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_incidents_filtered(client, viewer_headers):
    resp = client.get("/api/incidents?status=reported", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_incident(client, viewer_headers):
    resp = client.get("/api/incidents/1", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "assessing"


def test_create_incident_responder(client, responder_headers):
    payload = {
        "title": "New fire alert",
        "type": "fire",
        "barangay": "Poblacion",
        "severity": "critical",
        "description": "Market on fire",
        "affected_households": 5,
    }
    resp = client.post("/api/incidents", json=payload, headers=responder_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "reported"
    assert body["reported_by"] == "Responder"


def test_create_incident_denied_for_viewer(client, viewer_headers):
    payload = {"title": "X", "type": "flood", "barangay": "Poblacion", "severity": "low"}
    assert client.post("/api/incidents", json=payload, headers=viewer_headers).status_code == 403


def test_status_transition_via_patch(client, responder_headers):
    resp = client.patch("/api/incidents/1", json={"status": "responding"}, headers=responder_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "responding"


def test_invalid_status_transition(client, responder_headers):
    # "reported" -> "resolved" is not an allowed jump in one step.
    resp = client.post(
        "/api/incidents",
        json={"title": "Y", "type": "flood", "barangay": "San Roque", "severity": "high"},
        headers=responder_headers,
    )
    assert resp.status_code == 201
    incident_id = resp.json()["id"]
    resp = client.patch(f"/api/incidents/{incident_id}", json={"status": "resolved"}, headers=responder_headers)
    assert resp.status_code == 400