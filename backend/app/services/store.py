from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.core.barangays import SAN_RAFAEL_BARANGAYS
from app.db.session import SessionLocal
from app.models.center import EvacuationCenter
from app.models.household import Household
from app.models.incident import Incident
from app.models.resource import ResourceItem
from app.models.user import User

USERS = {
    "admin": {"id": 1, "username": "admin", "full_name": "Admin User", "role": "admin", "email": "admin@example.com"},
    "responder": {"id": 2, "username": "responder", "full_name": "Responder User", "role": "responder", "email": "responder@example.com"},
    "viewer": {"id": 3, "username": "viewer", "full_name": "Viewer User", "role": "viewer", "email": "viewer@example.com"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def serialize_household(model: Household) -> dict[str, Any]:
    return {
        "id": model.id,
        "household_no": model.household_no,
        "head_name": model.head_name,
        "address": model.address,
        "barangay": model.barangay,
        "size": model.size,
        "children_count": model.children_count,
        "elderly_count": model.elderly_count,
        "pwd_count": model.pwd_count,
        "contact": model.contact,
        "lat": model.lat,
        "lng": model.lng,
        "notes": model.notes,
    }


def serialize_center(model: EvacuationCenter) -> dict[str, Any]:
    facilities = model.facilities.split(",") if model.facilities else []
    return {
        "id": model.id,
        "name": model.name,
        "barangay": model.barangay,
        "address": model.address,
        "capacity": model.capacity,
        "current_occupants": model.current_occupants,
        "facilities": [facility.strip() for facility in facilities if facility.strip()],
        "contact": model.contact,
        "lat": model.lat,
        "lng": model.lng,
        "status": model.status,
    }


def serialize_resource(model: ResourceItem) -> dict[str, Any]:
    return {
        "id": model.id,
        "name": model.name,
        "type": model.type,
        "unit": model.unit,
        "quantity_on_hand": model.quantity_on_hand,
        "threshold": model.threshold,
        "expiry": model.expiry,
        "stored_in": model.stored_in,
        "updated_at": model.updated_at,
    }


def serialize_incident(model: Incident) -> dict[str, Any]:
    return {
        "id": model.id,
        "title": model.title,
        "type": model.type,
        "barangay": model.barangay,
        "severity": model.severity,
        "status": model.status,
        "description": model.description,
        "reported_at": model.reported_at,
        "updated_at": model.updated_at,
        "lat": model.lat,
        "lng": model.lng,
        "affected_households": model.affected_households,
        "reported_by": model.reported_by,
    }


def seed_demo_data():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add_all(
                [
                    User(id=1, username="admin", full_name="Admin User", role="admin", email="admin@example.com"),
                    User(id=2, username="responder", full_name="Responder User", role="responder", email="responder@example.com"),
                    User(id=3, username="viewer", full_name="Viewer User", role="viewer", email="viewer@example.com"),
                ]
            )

        if db.query(Household).count() == 0:
            db.add_all(
                [
                    Household(
                        household_no="H-001",
                        head_name="Maria Santos",
                        address="24 Rizal St",
                        barangay="Poblacion",
                        size=5,
                        children_count=2,
                        elderly_count=1,
                        pwd_count=0,
                        contact="09170001234",
                        lat=14.5995,
                        lng=120.9833,
                        notes="Needs wheelchair access",
                    ),
                    Household(
                        household_no="H-002",
                        head_name="Jose Dela Cruz",
                        address="12 Mabini Ave",
                        barangay="San Roque",
                        size=4,
                        children_count=1,
                        elderly_count=1,
                        pwd_count=1,
                        contact="09170005678",
                        lat=14.6101,
                        lng=120.9778,
                        notes="Two infants in household",
                    ),
                    Household(
                        household_no="H-003",
                        head_name="Alicia Ramos",
                        address="33 Luna Street",
                        barangay="Balagtas",
                        size=3,
                        children_count=1,
                        elderly_count=0,
                        pwd_count=0,
                        contact="09170009999",
                        lat=14.5912,
                        lng=120.9901,
                        notes="Senior caregiver on site",
                    ),
                ]
            )

        if db.query(EvacuationCenter).count() == 0:
            db.add_all(
                [
                    EvacuationCenter(
                        name="Poblacion Evacuation Center",
                        barangay="Poblacion",
                        address="San Jose Avenue",
                        capacity=120,
                        current_occupants=18,
                        facilities="kitchen,water,power",
                        contact="09180001111",
                        lat=14.596,
                        lng=120.985,
                        status="active",
                    ),
                    EvacuationCenter(
                        name="San Roque Relief Hub",
                        barangay="San Roque",
                        address="Mabini Extension",
                        capacity=80,
                        current_occupants=12,
                        facilities="water,power",
                        contact="09180002222",
                        lat=14.612,
                        lng=120.979,
                        status="active",
                    ),
                    EvacuationCenter(
                        name="Maronquillo Safe Haven",
                        barangay="Maronquillo",
                        address="Purok 3 Road",
                        capacity=60,
                        current_occupants=5,
                        facilities="kitchen,water",
                        contact="09180003333",
                        lat=14.620,
                        lng=120.975,
                        status="standby",
                    ),
                ]
            )

        if db.query(ResourceItem).count() == 0:
            db.add_all(
                [
                    ResourceItem(
                        name="Rice",
                        type="rice",
                        unit="kg",
                        quantity_on_hand=420,
                        threshold=300,
                        expiry="2027-01-15",
                        stored_in="Warehouse A",
                        updated_at="2026-09-25T10:00:00+00:00",
                    ),
                    ResourceItem(
                        name="Water",
                        type="water",
                        unit="liters",
                        quantity_on_hand=1500,
                        threshold=1200,
                        expiry="2027-02-01",
                        stored_in="Warehouse B",
                        updated_at="2026-09-25T10:00:00+00:00",
                    ),
                    ResourceItem(
                        name="Medicine",
                        type="medicine",
                        unit="boxes",
                        quantity_on_hand=80,
                        threshold=100,
                        expiry="2026-12-31",
                        stored_in="Clinic Store",
                        updated_at="2026-09-25T10:00:00+00:00",
                    ),
                    ResourceItem(
                        name="Blankets",
                        type="blankets",
                        unit="pieces",
                        quantity_on_hand=180,
                        threshold=160,
                        expiry=None,
                        stored_in="Relief Shelf",
                        updated_at="2026-09-25T10:00:00+00:00",
                    ),
                ]
            )

        if db.query(Incident).count() == 0:
            db.add_all(
                [
                    Incident(
                        title="Flooding near creek",
                        type="flood",
                        barangay="Balagtas",
                        severity="high",
                        status="responding",
                        description="Water level rising near the creek after heavy rain.",
                        reported_at="2026-09-24T08:15:00+00:00",
                        updated_at="2026-09-25T09:00:00+00:00",
                        lat=14.598,
                        lng=120.986,
                        affected_households=18,
                        reported_by="admin",
                    ),
                    Incident(
                        title="Electrical fire report",
                        type="fire",
                        barangay="Poblacion",
                        severity="moderate",
                        status="assessing",
                        description="Small electrical fire reported near a residential unit.",
                        reported_at="2026-09-25T06:45:00+00:00",
                        updated_at="2026-09-25T07:15:00+00:00",
                        lat=14.614,
                        lng=120.978,
                        affected_households=6,
                        reported_by="responder",
                    ),
                ]
            )

        db.commit()
    finally:
        db.close()


def get_households(barangay: str | None = None):
    db = SessionLocal()
    try:
        query = db.query(Household)
        if barangay:
            query = query.filter(Household.barangay.ilike(barangay))
        return [serialize_household(item) for item in query.order_by(Household.id).all()]
    finally:
        db.close()


def get_household(household_id: int):
    db = SessionLocal()
    try:
        item = db.query(Household).filter(Household.id == household_id).first()
        return serialize_household(item) if item else None
    finally:
        db.close()


def create_household(payload: dict[str, Any]):
    db = SessionLocal()
    try:
        item = Household(**payload)
        db.add(item)
        db.commit()
        db.refresh(item)
        return serialize_household(item)
    finally:
        db.close()


def update_household(household_id: int, payload: dict[str, Any]):
    db = SessionLocal()
    try:
        item = db.query(Household).filter(Household.id == household_id).first()
        if not item:
            return None
        for key, value in payload.items():
            if value is not None:
                setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return serialize_household(item)
    finally:
        db.close()


def delete_household(household_id: int):
    db = SessionLocal()
    try:
        item = db.query(Household).filter(Household.id == household_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


def import_households(csv_text: str):
    rows = list(csv.DictReader(io.StringIO(csv_text.strip())))
    if not rows:
        return {"created": 0, "items": []}

    created_items = []
    db = SessionLocal()
    try:
        for row in rows:
            payload = {
                "household_no": (row.get("household_no") or "").strip(),
                "head_name": (row.get("head_name") or "").strip(),
                "address": (row.get("address") or "").strip(),
                "barangay": (row.get("barangay") or "").strip(),
                "size": int((row.get("size") or 1) or 1),
                "children_count": int((row.get("children_count") or 0) or 0),
                "elderly_count": int((row.get("elderly_count") or 0) or 0),
                "pwd_count": int((row.get("pwd_count") or 0) or 0),
                "contact": (row.get("contact") or "").strip(),
                "lat": float(row.get("lat") or 0),
                "lng": float(row.get("lng") or 0),
                "notes": (row.get("notes") or "") or None,
            }
            if not payload["household_no"] or not payload["head_name"] or not payload["address"] or not payload["barangay"]:
                continue
            existing = db.query(Household).filter(Household.household_no == payload["household_no"]).first()
            if existing:
                continue
            item = Household(**payload)
            db.add(item)
            db.flush()
            created_items.append(serialize_household(item))
        db.commit()
        return {"created": len(created_items), "items": created_items}
    finally:
        db.close()


def get_centers():
    db = SessionLocal()
    try:
        return [serialize_center(item) for item in db.query(EvacuationCenter).order_by(EvacuationCenter.id).all()]
    finally:
        db.close()


def get_center(center_id: int):
    db = SessionLocal()
    try:
        item = db.query(EvacuationCenter).filter(EvacuationCenter.id == center_id).first()
        return serialize_center(item) if item else None
    finally:
        db.close()


def create_center(payload: dict[str, Any]):
    db = SessionLocal()
    try:
        facilities = payload.get("facilities") or []
        payload = {**payload, "facilities": ",".join(facilities)}
        item = EvacuationCenter(**payload)
        db.add(item)
        db.commit()
        db.refresh(item)
        return serialize_center(item)
    finally:
        db.close()


def update_center(center_id: int, payload: dict[str, Any]):
    db = SessionLocal()
    try:
        item = db.query(EvacuationCenter).filter(EvacuationCenter.id == center_id).first()
        if not item:
            return None
        if "facilities" in payload and isinstance(payload["facilities"], list):
            payload["facilities"] = ",".join(payload["facilities"])
        for key, value in payload.items():
            if value is not None:
                setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return serialize_center(item)
    finally:
        db.close()


def get_resources():
    db = SessionLocal()
    try:
        return [serialize_resource(item) for item in db.query(ResourceItem).order_by(ResourceItem.id).all()]
    finally:
        db.close()


def get_resource(resource_id: int):
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        return serialize_resource(item) if item else None
    finally:
        db.close()


def update_resource(resource_id: int, payload: dict[str, Any]):
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        if not item:
            return None
        for key, value in payload.items():
            if value is not None:
                setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return serialize_resource(item)
    finally:
        db.close()


def adjust_resource(resource_id: int, delta: int, reason: str | None = None):
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        if item is None:
            return None
        item.quantity_on_hand = max(0, item.quantity_on_hand + delta)
        item.updated_at = utc_now()
        db.commit()
        db.refresh(item)
        if reason:
            item.stored_in = item.stored_in or ""
        return serialize_resource(item)
    finally:
        db.close()


def get_resource_summaries():
    db = SessionLocal()
    try:
        grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"type": "other", "label": "Other", "total_on_hand": 0, "total_required": 0, "gap": 0, "low_stock_count": 0})
        for resource in db.query(ResourceItem).all():
            key = resource.type
            grouped[key]["type"] = resource.type
            grouped[key]["label"] = resource.name
            grouped[key]["total_on_hand"] += int(resource.quantity_on_hand)
            grouped[key]["total_required"] += int(resource.threshold)
            if resource.quantity_on_hand < resource.threshold:
                grouped[key]["low_stock_count"] += 1
        for item in grouped.values():
            item["gap"] = item["total_on_hand"] - item["total_required"]
        return [
            {
                "type": item["type"],
                "label": item["label"],
                "total_on_hand": item["total_on_hand"],
                "total_required": item["total_required"],
                "gap": item["gap"],
                "low_stock_count": item["low_stock_count"],
            }
            for item in grouped.values()
        ]
    finally:
        db.close()


def list_incidents():
    db = SessionLocal()
    try:
        return [serialize_incident(item) for item in db.query(Incident).order_by(Incident.id).all()]
    finally:
        db.close()


def get_incident(incident_id: int):
    db = SessionLocal()
    try:
        item = db.query(Incident).filter(Incident.id == incident_id).first()
        return serialize_incident(item) if item else None
    finally:
        db.close()


def create_incident(payload: dict[str, Any]):
    db = SessionLocal()
    try:
        now = utc_now()
        item = Incident(reported_at=now, updated_at=now, **payload)
        db.add(item)
        db.commit()
        db.refresh(item)
        return serialize_incident(item)
    finally:
        db.close()


def update_incident_status(incident_id: int, status: str):
    db = SessionLocal()
    try:
        item = db.query(Incident).filter(Incident.id == incident_id).first()
        if item is None:
            return None
        item.status = status
        item.updated_at = utc_now()
        db.commit()
        db.refresh(item)
        return serialize_incident(item)
    finally:
        db.close()


def calculate_allocation(barangay: str | None = None):
    households = get_households(barangay)
    db = SessionLocal()
    try:
        active_centers = [serialize_center(center) for center in db.query(EvacuationCenter).filter(EvacuationCenter.status != "closed").all()]
    finally:
        db.close()

    center_usage = {center["id"]: center["current_occupants"] for center in active_centers}
    assignments: list[dict[str, Any]] = []
    overflow: list[dict[str, Any]] = []
    coverage_gaps: list[str] = []

    for household in households:
        best_center = None
        best_distance = None
        for center in active_centers:
            remaining_capacity = center["capacity"] - center_usage.get(center["id"], 0)
            if remaining_capacity <= 0:
                continue
            distance = ((household["lat"] - center["lat"]) ** 2 + (household["lng"] - center["lng"]) ** 2) ** 0.5
            if best_center is None or distance < best_distance:
                best_center = center
                best_distance = distance

        if best_center is None:
            overflow.append(
                {
                    "household_id": household["id"],
                    "household_no": household["household_no"],
                    "head_name": household["head_name"],
                    "barangay": household["barangay"],
                    "reason": "No evacuation center has remaining capacity",
                }
            )
            continue

        center_usage[best_center["id"]] = center_usage.get(best_center["id"], 0) + 1
        assignments.append(
            {
                "id": len(assignments) + 1,
                "household_id": household["id"],
                "household_no": household["household_no"],
                "household_head": household["head_name"],
                "barangay": household["barangay"],
                "center_id": best_center["id"],
                "center_name": best_center["name"],
                "center_load_percent": int((center_usage[best_center["id"]] / best_center["capacity"]) * 100),
                "assigned_at": utc_now(),
            }
        )

    center_loads = []
    for center in active_centers:
        occupants = center_usage.get(center["id"], center["current_occupants"])
        load_percent = int((occupants / center["capacity"]) * 100) if center["capacity"] else 0
        if load_percent >= 100:
            status = "overflow"
        elif load_percent >= 90:
            status = "full"
        elif load_percent >= 70:
            status = "near_capacity"
        else:
            status = "ok"
        center_loads.append(
            {
                "center_id": center["id"],
                "center_name": center["name"],
                "barangay": center["barangay"],
                "capacity": center["capacity"],
                "occupants": occupants,
                "load_percent": load_percent,
                "status": status,
            }
        )

    if overflow:
        coverage_gaps.append(f"{len(overflow)} households could not be assigned due to full centers.")

    return {
        "request_id": f"alloc-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "generated_at": utc_now(),
        "total_households": len(households),
        "assigned_households": len(assignments),
        "overflow_households": len(overflow),
        "assignments": assignments,
        "center_loads": center_loads,
        "overflow": overflow,
        "coverage_gaps": coverage_gaps,
    }


def dashboard_stats():
    db = SessionLocal()
    try:
        households = [serialize_household(item) for item in db.query(Household).all()]
        incidents = [serialize_incident(item) for item in db.query(Incident).all()]
        centers = [serialize_center(item) for item in db.query(EvacuationCenter).all()]
        resources = [serialize_resource(item) for item in db.query(ResourceItem).all()]
    finally:
        db.close()

    vulnerable = sum(item["children_count"] + item["elderly_count"] + item["pwd_count"] for item in households)
    active_incidents = sum(1 for incident in incidents if incident["status"] != "resolved")
    critical_incidents = sum(1 for incident in incidents if incident["severity"] == "critical")
    available_capacity = sum(center["capacity"] - center["current_occupants"] for center in centers if center["status"] != "closed")
    low_stock_resources = sum(1 for resource in resources if resource["quantity_on_hand"] < resource["threshold"])
    assigned_households = len(calculate_allocation()["assignments"])
    return {
        "households": len(households),
        "vulnerable_members": vulnerable,
        "active_incidents": active_incidents,
        "critical_incidents": critical_incidents,
        "centers": len(centers),
        "available_capacity": available_capacity,
        "low_stock_resources": low_stock_resources,
        "assigned_households": assigned_households,
    }


def run_scenario(barangay: str, affected_households: int):
    allocation = calculate_allocation(barangay)
    db = SessionLocal()
    try:
        resources = [serialize_resource(item) for item in db.query(ResourceItem).all()]
    finally:
        db.close()
    resource_needs = []
    for resource in resources:
        factor = {"rice": 0.10, "water": 3, "medicine": 0.15, "blankets": 0.30}.get(resource["type"], 0.2)
        required = max(0, int(affected_households * factor))
        deficit = max(0, required - resource["quantity_on_hand"])
        if deficit == 0:
            status = "adequate"
        elif deficit > required * 0.5:
            status = "critical"
        else:
            status = "shortage"
        resource_needs.append(
            {
                "resource_id": resource["id"],
                "name": resource["name"],
                "current": resource["quantity_on_hand"],
                "required": required,
                "deficit": deficit,
                "unit": resource["unit"],
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
        "resource_needs": resource_needs,
    }

