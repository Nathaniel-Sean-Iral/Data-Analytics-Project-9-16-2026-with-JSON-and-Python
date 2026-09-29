"""Contract smoke tests: every core endpoint must answer with the expected HTTP
status for each role, so a bad wiring change fails loudly instead of silently
breaking the frontend."""

from __future__ import annotations

import pytest

# Method, path (id-based paths are exercised generically), roles allowed.
ROUTE_MATRIX: list[tuple[str, str, set[str]]] = [
    ("GET", "/api/health", {"anon", "admin", "responder", "viewer"}),
    ("GET", "/api/location", {"anon", "admin", "responder", "viewer"}),
    ("GET", "/api/households", {"admin", "responder", "viewer"}),
    ("GET", "/api/centers", {"admin", "responder", "viewer"}),
    ("GET", "/api/resources", {"admin", "responder", "viewer"}),
    ("GET", "/api/resources/summary", {"admin", "responder", "viewer"}),
    ("GET", "/api/incidents", {"admin", "responder", "viewer"}),
    ("GET", "/api/evacuations/center-loads", {"admin", "responder", "viewer"}),
    ("GET", "/api/dashboard/stats", {"admin", "responder", "viewer"}),
    ("GET", "/api/map/layers?layer=households", {"admin", "responder", "viewer"}),
    ("POST", "/api/households", {"admin", "responder"}),
    ("POST", "/api/centers", {"admin", "responder"}),
    ("POST", "/api/resources", {"admin", "responder"}),
    ("POST", "/api/incidents", {"admin", "responder"}),
    ("POST", "/api/evacuations/allocate", {"admin", "responder"}),
    ("POST", "/api/simulator/run", {"admin", "responder"}),
    ("POST", "/api/households/import", {"admin", "responder"}),
    ("POST", "/api/households/import/geojson", {"admin", "responder"}),
    ("POST", "/api/resources/adjust", {"admin", "responder"}),
    ("POST", "/api/map/zones", {"admin", "responder"}),
]

ROLE_HEADERS = {
    "admin": "admin_headers",
    "responder": "responder_headers",
    "viewer": "viewer_headers",
    "anon": "anon_headers",
}


@pytest.mark.parametrize("method,path,allowed", ROUTE_MATRIX)
def test_endpoint_authorization(method, path, allowed, request):
    client = request.getfixturevalue("client")
    for role, fixture in ROLE_HEADERS.items():
        headers = request.getfixturevalue(fixture)
        response = client.request(method, path, headers=headers, json={})

        if role in allowed:
            assert response.status_code in (
                200,
                201,
                202,
                400,
                409,
                422,
            ), f"{role} should reach {method} {path}, got {response.status_code}: {response.text[:300]}"
        elif role == "anon":
            # No credentials at all -> 401.
            assert response.status_code == 401, f"{role} must be rejected from {method} {path}, got {response.status_code}"
        else:
            # Authenticated but lacking the required role -> 403.
            assert (
                response.status_code == 403
            ), f"{role} must be forbidden from {method} {path}, got {response.status_code}"
