import math
from collections import defaultdict

from app.services.common import PER_PERSON_RATES, RESOURCE_TYPE_LABELS
from app.services.allocation import allocate


def run_scenario(db, barangay: str, affected_households: int) -> dict:
    """What-if calculation: project center loads and resource shortfalls."""
    from app.models.resource import Resource

    allocation = allocate(db, barangay=barangay)
    evacuees = affected_households * 4  # avg persons per household

    resources = db.query(Resource).order_by(Resource.id).all()
    needs = []
    for r in resources:
        rate = PER_PERSON_RATES.get(r.type, 0.05)
        required = math.ceil(evacuees * rate)
        deficit = max(0, required - r.quantity_on_hand)
        if deficit == 0:
            status = "adequate"
        elif deficit > required * 0.5:
            status = "critical"
        else:
            status = "shortage"
        needs.append(
            {
                "resource_id": r.id,
                "name": r.name,
                "current": r.quantity_on_hand,
                "required": required,
                "deficit": deficit,
                "unit": r.unit,
                "status": status,
            }
        )

    return {
        "scenario": {
            "title": f"{barangay} affected ({affected_households} households evacuees)",
            "barangay": barangay,
            "affected_households": affected_households,
        },
        "allocation": allocation,
        "resource_needs": needs,
    }


def resource_summaries(db) -> list[dict]:
    """Aggregate availability vs. required by resource type.

    `total_required` is the sum of thresholds per resource; scarcity is
    flagged when on hand < threshold.
    """
    from app.models.resource import Resource

    by_type: dict[str, dict] = defaultdict(lambda: {"on_hand": 0, "required": 0, "low": 0})

    for r in db.query(Resource).all():
        bucket = by_type[r.type]
        bucket["on_hand"] += r.quantity_on_hand
        bucket["required"] += r.threshold
        if r.quantity_on_hand < r.threshold:
            bucket["low"] += 1

    result = []
    for rtype, bucket in by_type.items():
        result.append(
            {
                "type": rtype,
                "label": RESOURCE_TYPE_LABELS.get(rtype, rtype.capitalize()),
                "total_on_hand": bucket["on_hand"],
                "total_required": bucket["required"],
                "gap": bucket["on_hand"] - bucket["required"],
                "low_stock_count": bucket["low"],
            }
        )
    return result


def dashboard_stats(db) -> dict:
    """Compute the operations dashboard snapshot."""
    from app.models.center import EvacuationCenter
    from app.models.incident import Incident
    from app.models.resource import Resource
    from app.models.household import Household

    households = db.query(Household).count()
    vulnerable = (
        db.query(Household)
        .with_entities(
            Household.children_count,
            Household.elderly_count,
            Household.pwd_count,
        )
        .all()
    )
    vulnerable_members = sum(c + e + p for c, e, p in vulnerable)

    incidents = db.query(Incident).all()
    active_incidents = [i for i in incidents if i.status != "resolved"]
    critical_incidents = [i for i in active_incidents if i.severity == "critical"]

    centers = db.query(EvacuationCenter).all()
    available_capacity = sum(max(0, c.capacity - c.current_occupants) for c in centers)

    low_stock = sum(1 for r in db.query(Resource).all() if r.quantity_on_hand < r.threshold)

    from app.models.evacuation import EvacuationAssignment

    assigned = db.query(EvacuationAssignment).count()
    return {
        "households": households,
        "vulnerable_members": vulnerable_members,
        "active_incidents": len(active_incidents),
        "critical_incidents": len(critical_incidents),
        "centers": len(centers),
        "available_capacity": available_capacity,
        "low_stock_resources": low_stock,
        "assigned_households": assigned,
    }