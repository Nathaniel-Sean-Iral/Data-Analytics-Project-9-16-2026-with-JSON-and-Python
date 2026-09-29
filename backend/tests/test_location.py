
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


def test_municipality_is_san_rafael_bulacan():
    assert MUNICIPALITY == "San Rafael"
    assert PROVINCE == "Bulacan"
    assert MUNICIPALITY_CENTER == (14.9571, 120.9629)


def test_every_barangay_has_a_centroid_inside_the_municipality():
    assert set(BARANGAY_CENTROIDS) == set(SAN_RAFAEL_BARANGAYS)
    for name, (lat, lng) in BARANGAY_CENTROIDS.items():
        assert is_within_municipality(lat, lng), f"{name} at {lat},{lng} is outside the municipality"


def test_coordinates_for_falls_back_to_the_town_center():
    lat, lng = coordinates_for("Not A Real Barangay")
    assert (lat, lng) == MUNICIPALITY_CENTER
    assert is_within_municipality(lat, lng)


def test_manila_and_caloocan_coordinates_are_outside_bounds():
    assert not is_within_municipality(14.5995, 120.9833)
    assert not is_within_municipality(14.08, 121.14)
    assert is_within_municipality(*MUNICIPALITY_CENTER)
    assert MUNICIPALITY_BOUNDS["min_lat"] < MUNICIPALITY_CENTER[0] < MUNICIPALITY_BOUNDS["max_lat"]


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
    assert data["center"] == {"lat": 14.9571, "lng": 120.9629}
    assert sorted(data["barangays"]) == sorted(SAN_RAFAEL_BARANGAYS)
    assert len(data["barangays"]) == 34
