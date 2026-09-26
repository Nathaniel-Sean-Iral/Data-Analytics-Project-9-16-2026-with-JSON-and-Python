def test_simulator_run(client, responder_headers):
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 100},
        headers=responder_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scenario"]["barangay"] == "Poblacion"
    assert body["scenario"]["affected_households"] == 100
    assert body["allocation"]["request_id"].startswith("ALLOC-")
    assert body["resource_needs"]

    by_type = {n["name"]: n for n in body["resource_needs"]}
    rice = by_type["Rice (50kg sack)"]
    # 100 households * 4 persons = 400 evacuees * 0.1 sacks = 40 required.
    assert rice["required"] == 40
    assert rice["current"] == 100
    assert rice["deficit"] == 0
    assert rice["status"] == "adequate"

    tents = by_type["Tents"]
    # 400 evacuees * 0.05 = 20 required > 12 on hand -> shortage.
    assert tents["required"] == 20
    assert tents["deficit"] == 8
    assert tents["status"] == "shortage"


def test_simulator_denied_for_viewer(client, viewer_headers):
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 10},
        headers=viewer_headers,
    )
    assert resp.status_code == 403