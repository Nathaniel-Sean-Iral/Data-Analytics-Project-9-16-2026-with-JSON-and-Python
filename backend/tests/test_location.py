
import re
from pathlib import Path

import pytest

from app.core.barangays import SAN_RAFAEL_BARANGAYS
from app.core.location import (
    BARANGAY_CENTROIDS,
    MUNICIPALITY,
    MUNICIPALITY_BOUNDS,
    MUNICIPALITY_CENTER,
    PROVINCE,
    coordinates_for,
    is_within_municipality,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Extent of the San Rafael boundary relation in OpenStreetMap (relation 8404894).
OSM_BOUNDS = {
    "min_lat": 14.9490398,
    "max_lat": 15.0410988,
    "min_lng": 120.8931033,
    "max_lng": 121.0595781,
}
OSM_CENTER = (14.9581176, 120.9636529)


def test_municipality_is_san_rafael_bulacan():
    assert MUNICIPALITY == "San Rafael"
    assert PROVINCE == "Bulacan"


def test_municipality_center_matches_openstreetmap():
    assert pytest.approx(OSM_CENTER, abs=0.001) == MUNICIPALITY_CENTER


def test_bounds_cover_the_openstreetmap_municipality_extent():
    for key in ("min_lat", "min_lng"):
        assert MUNICIPALITY_BOUNDS[key] <= OSM_BOUNDS[key], key
    for key in ("max_lat", "max_lng"):
        assert MUNICIPALITY_BOUNDS[key] >= OSM_BOUNDS[key], key
    assert MUNICIPALITY_BOUNDS["min_lat"] < MUNICIPALITY_CENTER[0] < MUNICIPALITY_BOUNDS["max_lat"]
    assert MUNICIPALITY_BOUNDS["min_lng"] < MUNICIPALITY_CENTER[1] < MUNICIPALITY_BOUNDS["max_lng"]


def test_every_barangay_has_a_centroid_inside_the_municipality():
    assert set(BARANGAY_CENTROIDS) == set(SAN_RAFAEL_BARANGAYS)
    for name, (lat, lng) in BARANGAY_CENTROIDS.items():
        assert is_within_municipality(lat, lng), f"{name} at {lat},{lng} is outside the municipality"


def test_barangay_centroids_are_distinct_and_not_all_piled_on_one_point():
    positions = {(round(lat, 4), round(lng, 4)) for lat, lng in BARANGAY_CENTROIDS.values()}
    assert len(positions) == len(SAN_RAFAEL_BARANGAYS)

    latitudes = [lat for lat, _ in BARANGAY_CENTROIDS.values()]
    longitudes = [lng for _, lng in BARANGAY_CENTROIDS.values()]
    # A ~152 km2 municipality is roughly 0.1 degrees across; guard against
    # collapsing the dataset onto a single invented point.
    assert max(latitudes) - min(latitudes) > 0.05
    assert max(longitudes) - min(longitudes) > 0.1


def test_coordinates_for_falls_back_to_the_town_center():
    lat, lng = coordinates_for("Not A Real Barangay")
    assert (lat, lng) == MUNICIPALITY_CENTER
    assert is_within_municipality(lat, lng)


def test_manila_and_caloocan_coordinates_are_outside_bounds():
    assert not is_within_municipality(14.5995, 120.9833)
    assert not is_within_municipality(14.08, 121.14)
    assert is_within_municipality(*MUNICIPALITY_CENTER)


def test_seeded_records_are_all_inside_san_rafael(client, admin_headers):
    for path in ["/api/households", "/api/centers", "/api/incidents"]:
        response = client.get(path, headers=admin_headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        records = payload["items"] if isinstance(payload, dict) else payload
        for record in records:
            lat, lng = record["lat"], record["lng"]
            assert is_within_municipality(lat, lng), f"{path} id={record['id']} at {lat},{lng}"


def test_location_endpoint_exposes_municipality_metadata(client):
    response = client.get("/api/location")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["municipality"] == "San Rafael"
    assert data["province"] == "Bulacan"
    assert data["label"] == "San Rafael, Bulacan"
    assert data["center"] == {"lat": MUNICIPALITY_CENTER[0], "lng": MUNICIPALITY_CENTER[1]}
    assert sorted(data["barangays"]) == sorted(SAN_RAFAEL_BARANGAYS)
    assert len(data["barangays"]) == 34


def test_frontend_location_mirrors_the_backend_reference_data():
    """The map reads the TS copies, so drift here silently misplaces the map."""
    location_ts = (REPO_ROOT / "frontend" / "src" / "lib" / "location.ts").read_text(encoding="utf-8")
    mock_ts = (REPO_ROOT / "frontend" / "src" / "api" / "mock.ts").read_text(encoding="utf-8")

    center = re.search(r"MUNICIPALITY_CENTER:\s*\[number, number\]\s*=\s*\[([\d.]+),\s*([\d.]+)\]", location_ts)
    assert center, "MUNICIPALITY_CENTER not found in location.ts"
    assert (float(center.group(1)), float(center.group(2))) == pytest.approx(
        MUNICIPALITY_CENTER, abs=0.0001
    )

    bounds = re.search(
        r"MUNICIPALITY_BOUNDS\s*=\s*\{(?P<body>[^}]*)\}", location_ts
    )
    assert bounds, "MUNICIPALITY_BOUNDS not found in location.ts"
    body = bounds.group("body")
    frontend_bounds = {
        "min_lat": float(re.search(r"minLat:\s*([\d.]+)", body).group(1)),
        "max_lat": float(re.search(r"maxLat:\s*([\d.]+)", body).group(1)),
        "min_lng": float(re.search(r"minLng:\s*([\d.]+)", body).group(1)),
        "max_lng": float(re.search(r"maxLng:\s*([\d.]+)", body).group(1)),
    }
    assert frontend_bounds == pytest.approx(MUNICIPALITY_BOUNDS, abs=0.0001)

    frontend_centroids: dict[str, tuple[float, float]] = {}
    for match in re.finditer(
        r"^\s*(?:'([^']+)'|([A-Za-z][A-Za-z0-9 .\-]*)):\s*\[\s*([\d.]+),\s*([\d.]+)\s*\],",
        mock_ts,
        flags=re.MULTILINE,
    ):
        name = match.group(1) or match.group(2).strip()
        frontend_centroids[name] = (float(match.group(3)), float(match.group(4)))

    assert set(frontend_centroids) == set(SAN_RAFAEL_BARANGAYS)
    for name, coordinates in frontend_centroids.items():
        assert coordinates == pytest.approx(BARANGAY_CENTROIDS[name], abs=0.0001), name
