"""Guards against permission drift between the backend and the frontend.

`frontend/src/lib/permissions.ts` mirrors the `require_roles(...)` guards used by
the API routers. Nothing enforces that the two stay in sync, so this module
asserts the frontend capability map against the routes actually registered on the
FastAPI app. When a guard changes, this test fails and names the capability that
needs updating.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

from app.core.config import settings
from app.main import app

PERMISSIONS_TS = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "permissions.ts"
)


def _all_api_routes() -> list[tuple[str, str, APIRoute]]:
    """Flatten the app's routes as (method, full_path, route) tuples.

    Routers are attached lazily, so `app.routes` holds wrapper objects rather
    than APIRoute instances. Each wrapper exposes the real routes on
    `original_router`; the configured API prefix is applied here because the
    router definitions themselves carry no prefix.

    The route objects are returned as-is and never mutated: they are shared with
    the TestClient, so rewriting `route.path` here would corrupt routing for
    every other test in the session.
    """
    found: list[tuple[str, str, APIRoute]] = []
    for entry in app.routes:
        if isinstance(entry, APIRoute):
            found.extend((m, entry.path, entry) for m in entry.methods)
            continue
        original = getattr(entry, "original_router", None)
        if original is None:
            continue
        for route in original.routes:
            if isinstance(route, APIRoute):
                full = f"{settings.API_PREFIX}{route.path}"
                found.extend((m, full, route) for m in route.methods)
    return found


API_ROUTES = _all_api_routes()

ROLES = ("admin", "responder", "viewer")

# Capability -> the endpoint that must enforce it. Several capabilities share an
# endpoint (e.g. household:create and household:import both POST /households
# family routes), so each entry is checked independently against its own route.
CAPABILITY_ROUTES: dict[str, tuple[str, str]] = {
    "household:create": ("POST", "/api/households"),
    "household:update": ("PUT", "/api/households/{household_id}"),
    "household:delete": ("DELETE", "/api/households/{household_id}"),
    "household:import": ("POST", "/api/households/import"),
    "center:create": ("POST", "/api/centers"),
    "center:update": ("PUT", "/api/centers/{center_id}"),
    "center:delete": ("DELETE", "/api/centers/{center_id}"),
    "resource:create": ("POST", "/api/resources"),
    "resource:update": ("PATCH", "/api/resources/{resource_id}"),
    "resource:delete": ("DELETE", "/api/resources/{resource_id}"),
    "incident:create": ("POST", "/api/incidents"),
    "incident:update": ("PUT", "/api/incidents/{incident_id}/status"),
    "incident:delete": ("DELETE", "/api/incidents/{incident_id}"),
    "zone:manage": ("POST", "/api/map/zones"),
    "allocation:run": ("POST", "/api/evacuations/allocate"),
    "simulator:run": ("POST", "/api/simulator/run"),
    "user:create": ("POST", "/api/auth/users"),
}


def _route_guard_roles(route: APIRoute) -> set[str] | None:
    """Roles explicitly allowed by require_roles on this route, else None."""
    for dep in route.dependant.dependencies:
        func = getattr(dep.call, "__name__", "")
        if func == "dependency" and dep.call.__module__ == "app.core.deps":
            closure = dep.call.__closure__ or ()
            for cell in closure:
                value = cell.cell_contents
                if isinstance(value, tuple) and value and all(isinstance(v, str) for v in value):
                    return set(value)
    return None


def _parse_frontend_capabilities() -> dict[str, set[str]]:
    """Extract {capability: {roles}} from the TypeScript capability map."""
    source = PERMISSIONS_TS.read_text(encoding="utf-8")

    def block(name: str) -> list[str]:
        match = re.search(
            rf"const {name}[^=]*=\s*\[(.*?)\];",
            source,
            re.DOTALL,
        )
        assert match, f"could not find {name} array in {PERMISSIONS_TS.name}"
        return re.findall(r"'([a-z]+:[a-z]+)'", match.group(1))

    viewer, responder, admin_only = block("READ_ONLY"), block("RESPONDER"), block("ADMIN_ONLY")
    return {
        "viewer": set(viewer),
        "responder": set(responder),
        "admin": set(responder) | set(admin_only),
    }


FRONTEND = _parse_frontend_capabilities()


def test_permissions_file_is_present():
    assert PERMISSIONS_TS.exists(), (
        f"{PERMISSIONS_TS} not found — the frontend capability map must stay in sync "
        "with the backend guards."
    )


@pytest.mark.parametrize("capability", sorted(CAPABILITY_ROUTES))
def test_capability_matches_backend_guard(capability: str):
    """Each capability must be granted to exactly the roles its route allows."""
    method, route_path = CAPABILITY_ROUTES[capability]

    matches = [r for verb, path, r in API_ROUTES if path == route_path and verb == method]
    assert matches, f"no {method} {route_path} route is registered"

    backend_roles = _route_guard_roles(matches[0])
    assert backend_roles is not None, (
        f"{method} {route_path} has no require_roles guard; update CAPABILITY_ROUTES in "
        "this test and permissions.ts to match reality."
    )

    frontend_roles = {role for role in ROLES if capability in FRONTEND[role]}
    assert frontend_roles == backend_roles, (
        f"{capability} drift: frontend grants {sorted(frontend_roles)} but "
        f"{method} {route_path} allows {sorted(backend_roles)}. "
        "Update frontend/src/lib/permissions.ts."
    )


def test_no_unknown_capabilities_in_frontend():
    """Every capability in the TS file must be covered by this test."""
    known = set(CAPABILITY_ROUTES)
    declared = set().union(*FRONTEND.values())
    assert declared <= known, f"uncovered capabilities: {sorted(declared - known)}"
