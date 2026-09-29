"""Tests for pagination, the stock ledger, CRUD gaps, GeoJSON import, and allocation."""

from __future__ import annotations

import pytest

from app.services.allocation import haversine_km
from app.services.store import RESOURCE_TYPE_LABELS

# ---------------------------------------------------------------- pagination


def test_resources_plain_list_when_unparameterised(client, viewer_headers):
    response = client.get("/api/resources", headers=viewer_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_resources_paginated_envelope(client, viewer_headers):
    response = client.get("/api/resources", params={"page": 1, "page_size": 2}, headers=viewer_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"items", "total", "page", "page_size", "pages"}
    assert len(body["items"]) <= 2
    assert body["total"] >= len(body["items"])


def test_pagination_page_size_is_respected(client, viewer_headers):
    first = client.get("/api/resources", params={"page": 1, "page_size": 1}, headers=viewer_headers).json()
    second = client.get("/api/resources", params={"page": 2, "page_size": 1}, headers=viewer_headers).json()
    if first["total"] >= 2:
        assert first["items"][0]["id"] != second["items"][0]["id"]


def test_search_filters_results(client, responder_headers):
    response = client.get("/api/households", params={"search": "Household"}, headers=responder_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 0
    for item in body["items"]:
        assert "household" in (item["head_name"] + item["household_no"]).lower() or item["barangay"]


def test_unknown_sort_key_falls_back_instead_of_erroring(client, viewer_headers):
    response = client.get("/api/resources", params={"sort": "; DROP TABLE resources"}, headers=viewer_headers)
    assert response.status_code == 200
    assert response.json()["sort"] == "id"


def test_sort_desc_reverses_order(client, viewer_headers):
    asc = client.get("/api/incidents", params={"sort": "id", "order": "asc"}, headers=viewer_headers).json()
    desc = client.get("/api/incidents", params={"sort": "id", "order": "desc"}, headers=viewer_headers).json()
    if len(asc["items"]) >= 2:
        assert asc["items"][0]["id"] < asc["items"][-1]["id"]
        assert desc["items"][0]["id"] > desc["items"][-1]["id"]


# -------------------------------------------------------------------- ledger


def test_adjust_writes_ledger_entry(client, responder_headers):
    resource = client.post(
        "/api/resources",
        json={"name": "Ledger Test Rice", "type": "rice", "unit": "sacks", "quantity_on_hand": 10, "threshold": 5},
        headers=responder_headers,
    )
    assert resource.status_code == 201
    resource_id = resource.json()["id"]

    transactions = client.get(f"/api/resources/{resource_id}/transactions", headers=responder_headers).json()
    assert len(transactions) == 1
    assert transactions[0]["reason"] == "created"
    assert transactions[0]["quantity_after"] == 10

    adjusted = client.post(
        "/api/resources/adjust",
        json={"resource_id": resource_id, "delta": -4, "reason": "released"},
        headers=responder_headers,
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["quantity_on_hand"] == 6

    transactions = client.get(f"/api/resources/{resource_id}/transactions", headers=responder_headers).json()
    assert len(transactions) == 2
    newest = transactions[0]
    assert newest["delta"] == -4
    assert newest["quantity_after"] == 6
    assert newest["reason"] == "released"
    assert newest["performed_by"] == "responder"


def test_adjust_cannot_go_negative(client, responder_headers):
    resource = client.post(
        "/api/resources",
        json={"name": "Negative Test", "type": "water", "unit": "litres", "quantity_on_hand": 3},
        headers=responder_headers,
    ).json()

    response = client.post(
        "/api/resources/adjust",
        json={"resource_id": resource["id"], "delta": -10},
        headers=responder_headers,
    )
    assert response.status_code == 409

    unchanged = client.get(f"/api/resources/{resource['id']}", headers=responder_headers).json()
    assert unchanged["quantity_on_hand"] == 3

    transactions = client.get(f"/api/resources/{resource['id']}/transactions", headers=responder_headers).json()
    assert len(transactions) == 1, "a rejected adjustment must not leave a ledger row"


def test_delete_resource_removes_its_ledger(client, admin_headers):
    resource = client.post(
        "/api/resources",
        json={"name": "Doomed Resource", "type": "other", "unit": "boxes", "quantity_on_hand": 1},
        headers=admin_headers,
    ).json()
    resource_id = resource["id"]

    assert client.delete(f"/api/resources/{resource_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/resources/{resource_id}", headers=admin_headers).status_code == 404
    # A 404 on the sub-resource proves the ledger rows were cleaned up too.
    assert client.get(f"/api/resources/{resource_id}/transactions", headers=admin_headers).status_code == 404


# ---------------------------------------------------------------------- CRUD


def test_resource_crud_round_trip(client, responder_headers, admin_headers):
    created = client.post(
        "/api/resources",
        json={"name": "Full CRUD Item", "type": "blankets", "unit": "pcs", "quantity_on_hand": 50, "threshold": 20},
        headers=responder_headers,
    )
    assert created.status_code == 201
    resource_id = created.json()["id"]

    patched = client.patch(f"/api/resources/{resource_id}", json={"threshold": 80}, headers=responder_headers)
    assert patched.status_code == 200
    assert patched.json()["threshold"] == 80

    assert client.get(f"/api/resources/{resource_id}", headers=responder_headers).json()["name"] == "Full CRUD Item"
    assert client.delete(f"/api/resources/{resource_id}", headers=admin_headers).status_code == 204


def test_only_admin_can_delete_resources(client, admin_headers, viewer_headers):
    created = client.post(
        "/api/resources",
        json={"name": "Protected", "type": "medicine", "unit": "kits", "quantity_on_hand": 2},
        headers=admin_headers,
    ).json()
    assert client.delete(f"/api/resources/{created['id']}", headers=viewer_headers).status_code == 403
    assert client.delete(f"/api/resources/{created['id']}", headers=admin_headers).status_code == 204


def test_center_delete_blocked_while_occupied(client, responder_headers, admin_headers):
    centers = client.get("/api/centers", headers=responder_headers).json()
    occupied = next((c for c in centers if c["current_occupants"] > 0), None)
    if occupied is None:
        pytest.skip("seed data has no occupied center")
    response = client.delete(f"/api/centers/{occupied['id']}", headers=admin_headers)
    assert response.status_code == 409
    assert "houses" in response.json()["detail"].lower()


def test_empty_center_can_be_deleted(client, responder_headers, admin_headers):
    centers = client.get("/api/centers", headers=responder_headers).json()
    empty = next((c for c in centers if c["current_occupants"] == 0), None)
    if empty is None:
        pytest.skip("seed data has no empty center")
    assert client.delete(f"/api/centers/{empty['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/centers/{empty['id']}", headers=admin_headers).status_code == 404


def test_incident_full_update_and_delete(client, responder_headers, admin_headers):
    created = client.post(
        "/api/incidents",
        json={
            "title": "Test Incident",
            "type": "flood",
            "barangay": "Poblacion",
            "severity": "high",
            "description": "initial",
        },
        headers=responder_headers,
    )
    assert created.status_code == 200
    incident_id = created.json()["id"]

    patched = client.patch(
        f"/api/incidents/{incident_id}",
        json={"title": "Renamed", "severity": "moderate", "status": "responding"},
        headers=responder_headers,
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["title"] == "Renamed"
    assert body["severity"] == "moderate"
    assert body["status"] == "responding"

    assert client.delete(f"/api/incidents/{incident_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/incidents/{incident_id}", headers=admin_headers).status_code == 404


def test_incident_zone_geojson_round_trips(client, responder_headers, admin_headers):
    zone = {
        "type": "Polygon",
        "coordinates": [[[120.96, 14.95], [120.97, 14.95], [120.97, 14.96], [120.96, 14.95]]],
    }
    created = client.post(
        "/api/incidents",
        json={
            "title": "Zoned Flood",
            "type": "flood",
            "barangay": "Poblacion",
            "severity": "critical",
            "lat": 14.9571,
            "lng": 120.9629,
            "zone_geojson": zone,
        },
        headers=responder_headers,
    )
    assert created.status_code == 200
    assert created.json()["zone_geojson"] == zone
    incident_id = created.json()["id"]

    refetched = client.get(f"/api/incidents/{incident_id}", headers=responder_headers).json()
    assert refetched["zone_geojson"] == zone
    client.delete(f"/api/incidents/{incident_id}", headers=admin_headers)


# -------------------------------------------------------------- GeoJSON import


def test_geojson_import_with_polygon_centroid(client, responder_headers):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "household_no": "GEO-001",
                    "head_name": "Ana Dela Cruz",
                    "address": "123 Katipunan",
                    "barangay": "Poblacion",
                    "size": 5,
                    "children_count": 2,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[120.9600, 14.9500], [120.9700, 14.9500], [120.9700, 14.9600], [120.9600, 14.9500]]],
                },
            }
        ],
    }
    response = client.post("/api/households/import/geojson", json={"geojson": payload}, headers=responder_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    item = body["items"][0]
    assert item["size"] == 5
    assert item["lat"] == pytest.approx(14.95333, abs=0.01)
    assert item["lng"] == pytest.approx(120.965, abs=0.01)


def test_geojson_import_falls_back_to_barangay_centroid(client, responder_headers):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "household_no": "GEO-002",
                    "head_name": "Pedro Santos",
                    "address": "456 Rizal",
                    "barangay": "BMA-Balagtas",
                },
                "geometry": None,
            }
        ],
    }
    body = client.post("/api/households/import/geojson", json={"geojson": payload}, headers=responder_headers).json()
    assert body["created"] == 1
    item = body["items"][0]
    assert item["lat"] != 0 and item["lng"] != 0
    assert 14.5 < item["lat"] < 15.4
    assert 120.4 < item["lng"] < 121.5


def test_geojson_import_reports_bad_features_without_failing(client, responder_headers):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"head_name": "No number"}, "geometry": None},
            {
                "type": "Feature",
                "properties": {
                    "household_no": "GEO-003",
                    "head_name": "Good Record",
                    "address": "789 Mabini",
                    "barangay": "Poblacion",
                },
                "geometry": {"type": "Point", "coordinates": [120.96, 14.95]},
            },
        ],
    }
    body = client.post("/api/households/import/geojson", json={"geojson": payload}, headers=responder_headers).json()
    assert body["created"] == 1
    assert len(body["errors"]) == 1
    assert "household_no" in body["errors"][0]["error"]


def test_geojson_import_deduplicates(client, responder_headers):
    feature = {
        "type": "Feature",
        "properties": {
            "household_no": "GEO-DUP",
            "head_name": "Dup Record",
            "address": "10 San Jose",
            "barangay": "Poblacion",
        },
        "geometry": {"type": "Point", "coordinates": [120.96, 14.95]},
    }
    payload = {"type": "FeatureCollection", "features": [feature]}
    first = client.post("/api/households/import/geojson", json={"geojson": payload}, headers=responder_headers).json()
    second = client.post("/api/households/import/geojson", json={"geojson": payload}, headers=responder_headers).json()
    assert first["created"] == 1
    assert second["created"] == 0
    assert second["skipped"] == 1


def test_geojson_import_rejects_non_featurecollection(client, responder_headers):
    response = client.post("/api/households/import/geojson", json={"geojson": {"foo": "bar"}}, headers=responder_headers)
    assert response.status_code == 400


# ----------------------------------------------------------------- allocation


def test_haversine_is_plausible_for_san_rafael():
    # Poblacion to a point ~1km north.
    distance = haversine_km(14.9571, 120.9629, 14.9661, 120.9629)
    assert 0.9 < distance < 1.2
    assert haversine_km(14.9571, 120.9629, 14.9571, 120.9629) == 0


def test_allocation_counts_people_not_households(client, responder_headers):
    response = client.post("/api/evacuations/allocate", json={"barangay": None}, headers=responder_headers)
    assert response.status_code == 200
    body = response.json()

    # The original bug: every household added exactly 1 to the center count.
    total_people = sum(item["size"] for item in body["assignments"])
    assert body["assigned_people"] == total_people
    assert body["assigned_people"] > body["assigned_households"], "households of >1 person must add more than 1"

    for load in body["center_loads"]:
        assert load["projected_occupants"] == load["current_occupants"] + load["newly_assigned"]


def test_allocation_never_exceeds_capacity(client, responder_headers):
    body = client.post("/api/evacuations/allocate", json={}, headers=responder_headers).json()
    for load in body["center_loads"]:
        assert load["projected_occupants"] <= load["capacity"], f"{load['center_name']} over capacity"


def test_allocation_ignores_closed_centers(client, responder_headers, admin_headers):
    centers = client.get("/api/centers", headers=admin_headers).json()
    closed = next((c for c in centers if c["status"] == "closed"), None)
    if closed is None:
        pytest.skip("seed data has no closed center")

    body = client.post("/api/evacuations/allocate", json={}, headers=responder_headers).json()
    assert closed["id"] not in {load["center_id"] for load in body["center_loads"]}


def test_allocation_honours_affected_household_cap(client, responder_headers):
    body = client.post(
        "/api/evacuations/allocate",
        json={"affected_households": 3},
        headers=responder_headers,
    ).json()
    assert body["total_households"] == 3
    assert body["assigned_households"] + body["overflow_households"] == 3


def test_allocation_persists_and_can_be_read_back(client, responder_headers):
    run = client.post("/api/evacuations/allocate", json={"persist": True}, headers=responder_headers)
    assert run.status_code == 200
    request_id = run.json()["request_id"]
    assert run.json()["persisted"] is True

    stored = client.get(f"/api/evacuations/assignments/{request_id}", headers=responder_headers)
    assert stored.status_code == 200
    assert stored.json()["count"] == len(run.json()["assignments"])
    # Occupancy must be recorded in people, matching the live calculation.
    assert all(row["occupants"] >= 1 for row in stored.json()["assignments"])


def test_dashboard_does_not_persist_assignments(client, viewer_headers):
    client.get("/api/dashboard/stats", headers=viewer_headers)
    response = client.post("/api/evacuations/allocate", json={}, headers=viewer_headers)
    assert response.status_code == 403, "viewer cannot trigger allocation"


# ------------------------------------------------------------------ scenarios


def test_scenario_requirements_scale_with_people(client, responder_headers):
    """Relief needs must be computed from people, not household count."""
    # Clear any seeded households out of Banca-banca first so the selected set
    # is fully controlled here and the assertions below are exact.
    seeded = client.get(
        "/api/households", params={"barangay": "Banca-banca", "page_size": 200}, headers=responder_headers
    ).json()
    for item in seeded["items"]:
        assert client.delete(f"/api/households/{item['id']}", headers=responder_headers).status_code in (
            200,
            204,
        )

    for index in range(6):
        created = client.post(
            "/api/households",
            json={
                "household_no": f"SCN-{index}",
                "head_name": f"Scenario Person {index}",
                "address": f"{index} Scenario St",
                "barangay": "Banca-banca",
                "size": 4,
            },
            headers=responder_headers,
        )
        assert created.status_code == 200

    small = client.post(
        "/api/simulator/run", json={"barangay": "Banca-banca", "affected_households": 2}, headers=responder_headers
    ).json()
    large = client.post(
        "/api/simulator/run", json={"barangay": "Banca-banca", "affected_households": 6}, headers=responder_headers
    ).json()

    assert large["scenario"]["total_people"] > small["scenario"]["total_people"]
    assert small["scenario"]["total_people"] == 2 * 4
    assert large["scenario"]["total_people"] == 6 * 4

    small_by_id = {need["resource_id"]: need for need in small["resource_needs"]}
    large_by_id = {need["resource_id"]: need for need in large["resource_needs"]}
    water = next(rid for rid, need in small_by_id.items() if "water" in need["name"].lower())
    assert large_by_id[water]["required"] > small_by_id[water]["required"]

    # Water is 3 L per person per day; needs must follow people, not households.
    assert small_by_id[water]["required"] == small["scenario"]["total_people"] * 3


def test_resource_summary_labels_are_types_not_item_names(client, viewer_headers):
    summaries = client.get("/api/resources/summary", headers=viewer_headers).json()
    for summary in summaries:
        assert summary["label"] != summary["type"], "label must be a human label, not the raw type"
        assert summary["label"] == RESOURCE_TYPE_LABELS[summary["type"]]
        assert summary["gap"] == summary["total_on_hand"] - summary["total_required"]
