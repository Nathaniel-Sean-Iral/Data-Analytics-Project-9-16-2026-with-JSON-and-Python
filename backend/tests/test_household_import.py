def test_admin_can_import_households_csv(client, admin_headers):
    payload = {
        "csv": """household_no,head_name,address,barangay,size,children_count,elderly_count,pwd_count,contact,lat,lng,notes
H-IMPORT-001,Juan Dela Cruz,12 Main Street,Poblacion,4,1,0,0,09170000001,14.9574,120.9634,Needs support
H-IMPORT-002,Maria Santos,9 Rizal Ave,San Roque,3,0,1,1,09170000002,14.9703,120.9785,Wheelchair access
"""
    }

    response = client.post("/api/households/import", json=payload, headers=admin_headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["created"] == 2
    assert data["items"][0]["household_no"] == "H-IMPORT-001"


def test_import_falls_back_to_barangay_centroid_when_coordinates_missing(client, admin_headers):
    payload = {
        "csv": """household_no,head_name,address,barangay,size,children_count,elderly_count,pwd_count,contact,lat,lng,notes
H-IMPORT-003,Ana Bautista,7 Katipunan St,Mabalas-balas,5,2,1,0,09170000003,,,No coordinates supplied
"""
    }

    response = client.post("/api/households/import", json=payload, headers=admin_headers)

    assert response.status_code == 200, response.text
    created = response.json()["items"]
    assert len(created) == 1
    from app.core.location import BARANGAY_CENTROIDS, is_within_municipality

    expected = BARANGAY_CENTROIDS["Mabalas-balas"]
    assert (created[0]["lat"], created[0]["lng"]) == expected
    assert is_within_municipality(created[0]["lat"], created[0]["lng"])
