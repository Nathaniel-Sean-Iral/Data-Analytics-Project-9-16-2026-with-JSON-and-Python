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
    # A simulation is a dry run, so it is tagged SIM- and never persisted.
    assert body["allocation"]["request_id"].startswith("SIM-")
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


def test_simulator_reports_estimated_evacuees(client, responder_headers):
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 100},
        headers=responder_headers,
    )
    body = resp.json()
    assert body["scenario"]["estimated_evacuees"] == 400


def test_simulator_allocation_reflects_requested_household_count(client, responder_headers):
    """Regression: the allocation used to ignore `affected_households`.

    It ran against whatever rows the registry happened to hold, so a scenario
    asking for 500 households reported "0 overflow" while simultaneously
    reporting a critical resource deficit. The projected allocation must now
    model exactly the requested number of households.
    """
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 500},
        headers=responder_headers,
    )
    assert resp.status_code == 200
    allocation = resp.json()["allocation"]
    assert allocation["total_households"] == 500
    # Total capacity across the two seeded centers is far below 500 * 4 pax.
    assert allocation["overflow_households"] > 0
    assert allocation["assigned_households"] + allocation["overflow_households"] == 500


def test_simulator_is_a_dry_run(client, responder_headers, admin_headers):
    """A simulation must not write `evacuation_assignments` rows."""
    before = client.get("/api/dashboard/stats", headers=admin_headers).json()["assigned_households"]
    client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 300},
        headers=responder_headers,
    )
    after = client.get("/api/dashboard/stats", headers=admin_headers).json()["assigned_households"]
    assert before == after


def test_simulator_saturates_centers_and_pushes_the_rest_to_overflow(client, responder_headers):
    """Larger scenarios fill centers to capacity, then spill into overflow.

    The seeded centers hold 45 + 5 = 50 free slots, so 10 households (40 pax)
    fit and 200 households (800 pax) cannot. Occupancy is capped by capacity
    rather than growing without bound.
    """

    def run(n):
        resp = client.post(
            "/api/simulator/run",
            json={"barangay": "Poblacion", "affected_households": n},
            headers=responder_headers,
        )
        return resp.json()["allocation"]

    small = run(10)
    large = run(200)

    assert small["overflow_households"] == 0
    assert large["overflow_households"] > 0
    assert large["total_households"] == 200
    assert large["assigned_households"] < 200

    # Occupancy never exceeds the centers' combined capacity.
    for allocation in (small, large):
        for center in allocation["center_loads"]:
            assert center["occupants"] <= center["capacity"]


def test_simulator_denied_for_viewer(client, viewer_headers):
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 10},
        headers=viewer_headers,
    )
    assert resp.status_code == 403


def test_simulator_rejects_non_positive_households(client, responder_headers):
    resp = client.post(
        "/api/simulator/run",
        json={"barangay": "Poblacion", "affected_households": 0},
        headers=responder_headers,
    )
    assert resp.status_code == 422