"""Tests for the deterministic demo dataset generators."""

from __future__ import annotations

import json

from app.core.barangays import SAN_RAFAEL_BARANGAYS
from app.core.location import is_within_municipality
from app.db.session import SessionLocal
from app.models.household import Household
from app.services.demo_data import (
    TARGET_HOUSEHOLDS,
    generate_centers,
    generate_households,
    generate_incidents,
    generate_resources,
)


def test_households_are_deterministic():
    assert generate_households() == generate_households()


def test_households_total_and_coverage():
    households = generate_households()
    assert len(households) == TARGET_HOUSEHOLDS
    covered = {record["barangay"] for record in households}
    assert covered == set(SAN_RAFAEL_BARANGAYS)


def test_households_are_valid():
    for record in generate_households():
        assert record["size"] >= 1
        vulnerable = record["children_count"] + record["elderly_count"] + record["pwd_count"]
        assert vulnerable <= record["size"], f"{record['household_no']} vulnerable > size"
        assert record["children_count"] >= 0
        assert record["elderly_count"] >= 0
        assert record["pwd_count"] >= 0
        assert is_within_municipality(record["lat"], record["lng"]), record["household_no"]
        assert record["contact"].startswith("09")
        assert len(record["contact"]) == 11


def test_household_numbers_are_unique():
    numbers = [record["household_no"] for record in generate_households()]
    assert len(numbers) == len(set(numbers))


def test_centers_are_valid():
    centers = generate_centers()
    assert len(centers) >= 8
    assert any(center["status"] == "closed" for center in centers), "an allocation test needs a closed center"
    for center in centers:
        assert center["capacity"] > 0
        assert 0 <= center["current_occupants"] <= center["capacity"]
        assert center["facilities"]
        assert is_within_municipality(center["lat"], center["lng"])
        assert center["barangay"] in SAN_RAFAEL_BARANGAYS


def test_resources_include_below_threshold_items():
    resources = generate_resources()
    assert len(resources) >= 8
    assert any(resource["quantity_on_hand"] < resource["threshold"] for resource in resources)


def test_incidents_carry_valid_zone_polygons():
    incidents = generate_incidents()
    assert len(incidents) == 3
    for incident in incidents:
        assert incident["type"] in {"flood", "fire", "earthquake", "landslide"}
        assert incident["severity"] in {"low", "moderate", "high", "critical"}
        geometry = json.loads(incident["zone_geojson"])
        assert geometry["type"] == "Polygon"
        ring = geometry["coordinates"][0]
        assert len(ring) >= 4
        assert ring[0] == ring[-1], "polygon ring must be closed"
        for lng, lat in ring:
            assert is_within_municipality(lat, lng)


def test_seed_repeats_without_duplication(client, admin_headers):
    from app.services.store import seed_demo_data

    db = SessionLocal()
    before = db.query(Household).count()
    db.close()

    seed_demo_data()
    seed_demo_data()

    db = SessionLocal()
    after = db.query(Household).count()
    db.close()
    assert after == before, "re-running the seed must not duplicate rows"

    stats = client.get("/api/dashboard/stats", headers=admin_headers).json()
    assert stats["centers"] >= 8
    assert stats["low_stock_resources"] >= 3

    summaries = client.get("/api/resources/summary", headers=admin_headers).json()
    assert len(summaries) >= 6

    zones = client.get("/api/map/layers", params={"layer": "zones"}, headers=admin_headers).json()
    assert len(zones["features"]) >= 3
