from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_can_import_households_csv():
    payload = {
        "csv": """household_no,head_name,address,barangay,size,children_count,elderly_count,pwd_count,contact,lat,lng,notes
H-IMPORT-001,Juan Dela Cruz,12 Main Street,Poblacion,4,1,0,0,09170000001,14.6000,120.9800,Needs support
H-IMPORT-002,Maria Santos,9 Rizal Ave,San Roque,3,0,1,1,09170000002,14.6100,120.9750,Wheelchair access
"""
    }

    response = client.post(
        "/api/households/import",
        json=payload,
        headers={"Authorization": "Bearer mock-token-admin"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["created"] == 2
    assert data["items"][0]["household_no"] == "H-IMPORT-001"
