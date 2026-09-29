from __future__ import annotations

import math
import time
from typing import Any

from app.db.session import SessionLocal
from app.models.assignment import EvacuationAssignment
from app.models.center import EvacuationCenter
from app.models.household import Household
from app.models.incident import Incident

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres.

    The previous implementation compared raw degree deltas, which is only valid
    near the equator and distorted at Bulacan's latitude. It also mixed latitude
    into the x term and longitude into the y term.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _severity_weight(severity: str) -> int:
    return {"critical": 4, "high": 3, "moderate": 2, "low": 1}.get(severity, 0)


def _choose_households(
    households: list[Household],
    incidents: list[Incident],
    affected_households: int | None,
    target_barangay: str | None,
) -> tuple[list[Household], list[Household]]:
    """Split households into the set to place and the rest.

    When a specific household count is requested, the highest-risk households win
    by vulnerability score. Otherwise every active household in scope is placed.
    """
    in_scope = households
    if target_barangay:
        in_scope = [household for household in in_scope if household.barangay == target_barangay]

    if affected_households is None or affected_households >= len(in_scope):
        return in_scope, []

    # Risk score: vulnerable members first, then households in active incident zones.
    zone_barangays: dict[str, int] = {}
    for incident in incidents:
        if incident.status in {"resolved"}:
            continue
        zone_barangays[incident.barangay] = max(
            zone_barangays.get(incident.barangay, 0),
            _severity_weight(incident.severity),
        )

    def score(household: Household) -> tuple[int, int, int]:
        vulnerable = (household.children_count or 0) + (household.elderly_count or 0) + (household.pwd_count or 0)
        return (zone_barangays.get(household.barangay, 0), vulnerable, household.size or 1)

    ranked = sorted(in_scope, key=score, reverse=True)
    return ranked[:affected_households], ranked[affected_households:]


def calculate_allocation(
    barangay: str | None = None,
    affected_households: int | None = None,
    persist: bool = False,
) -> dict[str, Any]:
    """Assign households to evacuation centers, nearest-first.

    Occupancy is counted in *people*, not households: a household of six consumes
    six places. Centers are also checked so a household is never split across two
    centers.

    ``persist=True`` writes the result to ``evacuation_assignments`` under a single
    request id so a run can be reviewed or rolled back. The dashboard leaves this
    off, because a read-only stat should not create rows.
    """
    from app.services.store import utc_now, utc_now_dt

    db = SessionLocal()
    try:
        households = db.query(Household).filter(Household.is_active.is_(True)).all()
        incidents = db.query(Incident).all()
        centers = db.query(EvacuationCenter).filter(EvacuationCenter.status != "closed").all()

        to_place, excluded = _choose_households(households, incidents, affected_households, barangay)
        excluded_barangays = sorted({household.barangay for household in excluded})

        center_state = {
            center.id: {
                "center": center,
                "capacity": center.capacity or 0,
                "used": center.current_occupants or 0,
            }
            for center in centers
        }

        # Nearest center first, then the largest remaining space, so nearby
        # households do not all pile into the single closest facility.
        def rank(household: Household) -> list[tuple[float, int, int]]:
            scored = []
            for center_id, state in center_state.items():
                center = state["center"]
                if center.lat is None or center.lng is None or household.lat is None or household.lng is None:
                    continue
                distance = haversine_km(household.lat, household.lng, center.lat, center.lng)
                remaining = state["capacity"] - state["used"]
                if remaining <= 0:
                    continue
                scored.append((distance, -remaining, center_id))
            return sorted(scored)

        assignments: list[dict[str, Any]] = []
        overflow: list[dict[str, Any]] = []
        request_id = f"alloc-{int(time.time())}"
        now = utc_now()
        now_dt = utc_now_dt()
        db_rows: list[EvacuationAssignment] = []

        for household in to_place:
            members = max(1, household.size or 1)
            options = rank(household)
            target = None
            for distance, _negative_remaining, center_id in options:
                state = center_state[center_id]
                if state["capacity"] - state["used"] >= members:
                    target = (center_id, state, distance)
                    break

            if target is None:
                reason = (
                    "No evacuation center within the municipality has capacity for "
                    f"{members} people"
                )
                overflow.append(
                    {
                        "household_id": household.id,
                        "household_no": household.household_no,
                        "head_name": household.head_name,
                        "barangay": household.barangay,
                        "size": members,
                        "reason": reason,
                    }
                )
                continue

            center_id, state, distance = target
            state["used"] += members
            center = state["center"]
            load_percent = int((state["used"] / state["capacity"]) * 100) if state["capacity"] else 100
            assignments.append(
                {
                    "household_id": household.id,
                    "household_no": household.household_no,
                    "household_head": household.head_name,
                    "barangay": household.barangay,
                    "size": members,
                    "center_id": center_id,
                    "center_name": center.name,
                    "distance_km": round(distance, 2),
                    "center_load_percent": load_percent,
                    "assigned_at": now,
                }
            )
            db_rows.append(
                EvacuationAssignment(
                    request_id=request_id,
                    household_id=household.id,
                    center_id=center_id,
                    occupants=members,
                    distance_km=round(distance, 4),
                    status="assigned",
                    assigned_at=now_dt,
                )
            )

        center_loads = []
        for center_id, state in center_state.items():
            center = state["center"]
            capacity = state["capacity"]
            occupants = state["used"]
            load_percent = int((occupants / capacity) * 100) if capacity else 100
            if capacity == 0:
                status = "no_capacity"
            elif load_percent >= 100:
                status = "overflow"
            elif load_percent >= 90:
                status = "full"
            elif load_percent >= 70:
                status = "near_capacity"
            else:
                status = "ok"
            center_loads.append(
                {
                    "center_id": center_id,
                    "center_name": center.name,
                    "barangay": center.barangay,
                    "capacity": capacity,
                    "current_occupants": center.current_occupants or 0,
                    "projected_occupants": occupants,
                    "newly_assigned": occupants - (center.current_occupants or 0),
                    "remaining_capacity": max(0, capacity - occupants),
                    "load_percent": load_percent,
                    "status": status,
                }
            )

        if persist:
            db.add_all(db_rows)
            db.commit()

        total_people = sum(item["size"] for item in assignments)
        coverage_gaps: list[str] = []
        if overflow:
            coverage_gaps.append(
                f"{len(overflow)} households ({sum(item['size'] for item in overflow)} people) "
                "could not be assigned: no center had a contiguous place for them."
            )
        if excluded_barangays:
            coverage_gaps.append(
                f"Scope limited to {affected_households} households by risk ranking; "
                f"{len(excluded)} households in {', '.join(excluded_barangays)} were not placed."
            )
        unplaced_people = sum(item["size"] for item in overflow)
        total_capacity = sum(state["capacity"] for state in center_state.values())
        if unplaced_people:
            coverage_gaps.append(
                f"Total evacuation capacity is {total_capacity} people; "
                f"{unplaced_people} could not be placed."
            )

        return {
            "request_id": request_id,
            "generated_at": now,
            "barangay": barangay,
            "total_households": len(to_place),
            "total_people": sum(item["size"] for item in assignments) + sum(
                item["size"] for item in overflow
            ),
            "assigned_households": len(assignments),
            "assigned_people": total_people,
            "overflow_households": len(overflow),
            "assignments": assignments,
            "center_loads": sorted(center_loads, key=lambda item: -item["load_percent"]),
            "overflow": overflow,
            "coverage_gaps": coverage_gaps,
            "persisted": persist,
        }
    finally:
        db.close()


def get_assignment_run(request_id: str) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.query(EvacuationAssignment).filter(EvacuationAssignment.request_id == request_id).all()
        return [
            {
                "household_id": row.household_id,
                "household_no": row.household.household_no if row.household else None,
                "center_id": row.center_id,
                "center_name": row.center.name if row.center else None,
                "occupants": row.occupants,
                "distance_km": row.distance_km,
                "status": row.status,
                "assigned_at": row.assigned_at.isoformat() if row.assigned_at else None,
            }
            for row in rows
        ]
    finally:
        db.close()


def resource_requirements(total_people: int) -> dict[str, float]:
    """Per-person relief factor used by the scenario simulator.

    ``water`` is litres per person per day; the rest are per-person totals over a
    three-day response window.
    """
    return {
        "rice": 0.5,
        "water": 3.0,
        "medicine": 0.15,
        "blankets": 0.5,
        "hygiene": 0.25,
        "canned_goods": 0.4,
        "clothing": 0.3,
        "mats": 1.0,
        "tents": 0.1,
    }
