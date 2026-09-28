import math
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AffectedHousehold:
    """A household awaiting evacuation.

    Used both for real `Household` rows and for synthetic households projected by
    the scenario simulator, so a what-if run can model more evacuees than the
    registry currently holds.
    """

    id: int
    household_no: str
    head_name: str
    barangay: str
    size: int
    lat: float
    lng: float


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def coord_distance_km(lat1, lng1, lat2, lng2) -> float:
    return haversine_km(float(lat1 or 0), float(lng1 or 0), float(lat2 or 0), float(lng2 or 0))


def _active_centers(db):
    from app.models.center import EvacuationCenter

    return (
        db.query(EvacuationCenter)
        .filter(EvacuationCenter.status.in_(["active", "standby"]))
        .order_by(EvacuationCenter.id)
        .all()
    )


def _plan(
    households: list[AffectedHousehold],
    centers: list,
    request_id: str,
    generated_at: datetime,
) -> dict:
    """Pure nearest-center-first assignment. Touches no database session.

    Households needing `size` slots prefer a center that can still hold them
    whole; ties break on geographic distance. Anything that cannot be placed
    whole lands in the overflow list rather than being split across centers.
    """
    # Remaining slots per center (capacity - current occupants).
    slots = {c.id: max(0, c.capacity - c.current_occupants) for c in centers}
    # Track projected occupants for center-load reporting.
    occupants = {c.id: c.current_occupants for c in centers}

    assignments: list[dict] = []
    overflow: list[dict] = []
    barangays_with_centers = {c.barangay for c in centers}

    for h in households:
        candidates = sorted(
            centers,
            key=lambda c: (
                0 if slots[c.id] >= h.size or slots[c.id] > 0 else 1,  # with room first
                coord_distance_km(h.lat, h.lng, c.lat, c.lng),
            ),
        )
        chosen = None
        for c in candidates:
            if slots[c.id] >= h.size:
                chosen = c
                break
        if chosen is None:
            overflow.append(
                {
                    "household_id": h.id,
                    "household_no": h.household_no,
                    "head_name": h.head_name,
                    "barangay": h.barangay,
                    "reason": "No evacuation center with sufficient remaining capacity",
                }
            )
            continue

        slots[chosen.id] -= h.size
        occupants[chosen.id] += h.size
        load_pct = round((occupants[chosen.id] / chosen.capacity) * 100) if chosen.capacity else 100
        assignments.append(
            {
                "household_id": h.id,
                "household_no": h.household_no,
                "household_head": h.head_name,
                "barangay": h.barangay,
                "center_id": chosen.id,
                "center_name": chosen.name,
                "center_load_percent": load_pct,
                "assigned_at": generated_at,
            }
        )

    center_loads = []
    for c in centers:
        live_occupants = occupants[c.id]
        pct = round((live_occupants / c.capacity) * 100) if c.capacity else 100
        if pct >= 100:
            status = "overflow"
        elif pct >= 90:
            status = "full"
        elif pct >= 70:
            status = "near_capacity"
        else:
            status = "ok"
        center_loads.append(
            {
                "center_id": c.id,
                "center_name": c.name,
                "barangay": c.barangay,
                "capacity": c.capacity,
                "occupants": live_occupants,
                "load_percent": pct,
                "status": status,
            }
        )

    # Coverage gaps: barangays that have households but no evacuation center.
    affected_barangays = {h.barangay for h in households}
    gaps = [
        f"{b} has no evacuation center — pre-position transport assets."
        for b in sorted(affected_barangays - barangays_with_centers)
    ]

    return {
        "request_id": request_id,
        "generated_at": generated_at,
        "total_households": len(households),
        "assigned_households": len(assignments),
        "overflow_households": len(overflow),
        "assignments": assignments,
        "center_loads": center_loads,
        "overflow": overflow,
        "coverage_gaps": gaps,
    }


def allocate(db, barangay: str | None = None):
    """Assign affected households to the nearest evacuation center with room.

    Assigns every household currently in the registry, then persists the plan to
    `evacuation_assignments`. For a what-if run over a hypothetical number of
    affected households use `project_allocation` instead, which does not persist.
    """
    from app.models.evacuation import EvacuationAssignment
    from app.models.household import Household

    query = db.query(Household)
    if barangay:
        query = query.filter(Household.barangay == barangay)
    households = [
        AffectedHousehold(
            id=h.id,
            household_no=h.household_no,
            head_name=h.head_name,
            barangay=h.barangay,
            size=h.size,
            lat=h.lat,
            lng=h.lng,
        )
        for h in query.order_by(Household.household_no).all()
    ]

    centers = _active_centers(db)

    request_id = f"ALLOC-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    result = _plan(households, centers, request_id, datetime.now(timezone.utc))

    rows: list[EvacuationAssignment] = []
    for a in result["assignments"]:
        row = EvacuationAssignment(
            request_id=request_id,
            household_id=a["household_id"],
            center_id=a["center_id"],
        )
        db.add(row)
        rows.append(row)
    if rows:
        db.commit()
        for row, a in zip(rows, result["assignments"]):
            db.refresh(row)
            a["id"] = row.id

    return result


def project_allocation(db, barangay: str, affected_households: int) -> dict:
    """Dry-run allocation for a hypothetical number of affected households.

    Models exactly `affected_households` households in `barangay`, padding the
    registry's real households with synthetic ones anchored at the barangay's
    centroid, so the projected center loads and overflow actually reflect the
    scenario input. Nothing is written to the database.
    """
    from app.core.config import settings
    from app.models.household import Household

    real = (
        db.query(Household)
        .filter(Household.barangay == barangay)
        .order_by(Household.household_no)
        .all()
    )
    households = [
        AffectedHousehold(
            id=h.id,
            household_no=h.household_no,
            head_name=h.head_name,
            barangay=h.barangay,
            size=h.size,
            lat=h.lat,
            lng=h.lng,
        )
        for h in real
    ]

    # Anchor projected households on the barangay centroid; fall back to the mean
    # center position when the registry has no coordinates for the barangay yet.
    if real:
        anchor_lat = sum(float(h.lat or 0) for h in real) / len(real)
        anchor_lng = sum(float(h.lng or 0) for h in real) / len(real)
    else:
        centers = _active_centers(db)
        if centers:
            anchor_lat = sum(float(c.lat or 0) for c in centers) / len(centers)
            anchor_lng = sum(float(c.lng or 0) for c in centers) / len(centers)
        else:
            anchor_lat = anchor_lng = 0.0

    size = max(1, settings.avg_persons_per_household)
    for i in range(affected_households - len(households)):
        households.append(
            AffectedHousehold(
                id=-(i + 1),  # negative ids mark projected (non-persisted) households
                household_no=f"PROJ-{i + 1:04d}",
                head_name="Projected household",
                barangay=barangay,
                size=size,
                lat=anchor_lat,
                lng=anchor_lng,
            )
        )

    request_id = f"SIM-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    return _plan(households, _active_centers(db), request_id, datetime.now(timezone.utc))


def center_loads(db) -> list[dict]:
    """Current center occupancy (no allocation computed)."""
    from app.models.center import EvacuationCenter

    centers = db.query(EvacuationCenter).order_by(EvacuationCenter.id).all()
    result = []
    for c in centers:
        pct = round((c.current_occupants / c.capacity) * 100) if c.capacity else 100
        if pct >= 100:
            status = "overflow"
        elif pct >= 90:
            status = "full"
        elif pct >= 70:
            status = "near_capacity"
        else:
            status = "ok"
        result.append(
            {
                "center_id": c.id,
                "center_name": c.name,
                "barangay": c.barangay,
                "capacity": c.capacity,
                "occupants": c.current_occupants,
                "load_percent": pct,
                "status": status,
            }
        )
    return result