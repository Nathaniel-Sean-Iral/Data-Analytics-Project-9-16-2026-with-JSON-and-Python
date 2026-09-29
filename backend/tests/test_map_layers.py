"""Tests for the GeoJSON map layer endpoints."""

from __future__ import annotations


def test_households_layer_is_geojson(client, responder_headers):
    body = client.get("/api/map/layers", params={"layer": "households"}, headers=responder_headers).json()
    assert body["type"] == "FeatureCollection"
    assert body["layer"] == "households"
    assert isinstance(body["features"], list)
    assert len(body["features"]) >= 1
    feature = body["features"][0]
    assert feature["geometry"]["type"] == "Point"
    lng, lat = feature["geometry"]["coordinates"]
    assert 120.4 < lng < 121.5
    assert 14.5 < lat < 15.4


def test_centers_layer_reports_load(client, responder_headers):
    body = client.get("/api/map/layers", params={"layer": "centers"}, headers=responder_headers).json()
    assert len(body["features"]) >= 1
    props = body["features"][0]["properties"]
    assert "load_percent" in props
    assert 0 <= props["load_percent"] <= 100


def test_incidents_layer(client, responder_headers):
    body = client.get("/api/map/layers", params={"layer": "incidents"}, headers=responder_headers).json()
    assert "features" in body


def test_zones_layer_returns_incident_polygons(client, responder_headers, admin_headers):
    zone = {
        "type": "Polygon",
        "coordinates": [[[120.96, 14.95], [120.97, 14.95], [120.97, 14.96], [120.96, 14.95]]],
    }
    incident = client.post(
        "/api/incidents",
        json={
            "title": "Map Zone Test",
            "type": "flood",
            "barangay": "Poblacion",
            "severity": "critical",
            "zone_geojson": zone,
        },
        headers=responder_headers,
    ).json()

    body = client.get("/api/map/layers", params={"layer": "zones"}, headers=responder_headers).json()
    match = [f for f in body["features"] if f["properties"]["id"] == incident["id"]]
    assert len(match) == 1
    assert match[0]["geometry"]["type"] == "Polygon"

    client.delete(f"/api/incidents/{incident['id']}", headers=admin_headers)


def test_zone_can_be_saved_via_map_endpoint(client, responder_headers, admin_headers):
    incident = client.post(
        "/api/incidents",
        json={
            "title": "Zone Save Test",
            "type": "typhoon",
            "barangay": "Poblacion",
            "severity": "moderate",
        },
        headers=responder_headers,
    ).json()

    polygon = {"type": "Polygon", "coordinates": [[[120.96, 14.95], [120.97, 14.95], [120.97, 14.96], [120.96, 14.95]]]}
    response = client.post(
        "/api/map/zones",
        json={"incident_id": incident["id"], "geometry": polygon},
        headers=responder_headers,
    )
    assert response.status_code == 200
    assert response.json()["zone_geojson"] == polygon

    client.delete(f"/api/incidents/{incident['id']}", headers=admin_headers)


def test_layer_requires_valid_layer_name(client, viewer_headers):
    assert (
        client.get("/api/map/layers", params={"layer": "nope"}, headers=viewer_headers).status_code == 422
    )


def test_layer_is_protected(client):
    assert client.get("/api/map/layers", params={"layer": "centers"}).status_code == 401
