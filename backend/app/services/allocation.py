import math
from datetime import datetime, timezone


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometers."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def coord_distance_km(lat1, lng1, lat2, lng2) -> float:
    return haversine_km(float(lat1 or 0), float(lng1 or 0), float(lat2 or 0), float(lng2 or 0))


def allocate(db, barangay: str | None = None):
    """Assign affected households to the nearest evacuation center with room.

    Returns a dict matching AllocationResultOut plus the assignments to persist.
    """
    from app.models.center import EvacuationCenter
    from app.models.evacuation import EvacuationAssignment
    from app.models.household import Household

    query = db.query(Household)
    if barangay:
        query = query.filter(Household.barangay == barangay)
    households = query.order_by(Household.household_no).all()

    centers = (
        db.query(EvacuationCenter)
        .filter(EvacuationCenter.status.in_(["active", "standby"]))
        .order_by(EvacuationCenter.id)
        .all()
    )

    request_id = f"ALLOC-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    generated_at = datetime.now(timezone.utc)

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

    rows: list[EvacuationAssignment] = []
    for a in assignments:
        row = EvacuationAssignment(
            request_id=request_id,
            household_id=a["household_id"],
            center_id=a["center_id"],
        )
        db.add(row)
        rows.append(row)
    if assignments:
        db.commit()
        for row, a in zip(rows, assignments):
            db.refresh(row)
            a["id"] = row.id

    result = {
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
    return result


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