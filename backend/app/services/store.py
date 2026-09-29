from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.location import coordinates_for
from app.core.security import hash_password, needs_rehash, verify_password
from app.db.session import SessionLocal
from app.models.assignment import EvacuationAssignment
from app.models.center import EvacuationCenter
from app.models.household import Household
from app.models.incident import Incident
from app.models.resource import ResourceItem
from app.models.resource_transaction import ResourceTransaction
from app.models.user import User
from app.services.pagination import PageParams, apply_sort_and_search, build_page

DEMO_USERS = [
    {"id": 1, "username": "admin", "full_name": "Admin User", "role": "admin", "email": "admin@sanrafael.gov.ph"},
    {
        "id": 2,
        "username": "responder",
        "full_name": "Responder User",
        "role": "responder",
        "email": "responder@sanrafael.gov.ph",
    },
    {"id": 3, "username": "viewer", "full_name": "Viewer User", "role": "viewer", "email": "viewer@sanrafael.gov.ph"},
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def utc_now_dt() -> datetime:
    """Timezone-aware datetime, for real DateTime columns.

    ``utc_now`` returns a string because ``Incident.reported_at`` is a string
    column. Do not use it for DateTime columns; SQLite will reject a str.
    """
    return datetime.now(UTC)


def serialize_user(model: User) -> dict[str, Any]:
    return {
        "id": model.id,
        "username": model.username,
        "full_name": model.full_name,
        "role": model.role,
        "email": model.email,
        "is_active": model.is_active,
    }


def get_user_by_username(username: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        model = db.query(User).filter(User.username == username).first()
        return serialize_user(model) if model else None
    finally:
        db.close()


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        model = db.query(User).filter(User.username == username).first()
        if model is None or not model.is_active:
            return None
        if not verify_password(password, model.password_hash):
            return None
        if needs_rehash(model.password_hash):
            model.password_hash = hash_password(password)
            db.commit()
        return serialize_user(model)
    finally:
        db.close()


def create_user(payload: dict[str, Any], password: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == payload["username"]).first()
        if existing is not None:
            raise ValueError(f"Username '{payload['username']}' is already taken")
        model = User(
            username=payload["username"],
            full_name=payload["full_name"],
            role=payload.get("role", "viewer"),
            email=payload.get("email"),
            password_hash=hash_password(password),
            is_active=payload.get("is_active", True),
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return serialize_user(model)
    finally:
        db.close()


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
        "zone_geojson": json.loads(model.zone_geojson) if model.zone_geojson else None,
        "affected_households": model.affected_households,
        "reported_by": model.reported_by,
    }


def seed_demo_data():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            demo_password_hash = hash_password(settings.DEMO_PASSWORD)
            db.add_all(
                [
                    User(
                        id=record["id"],
                        username=record["username"],
                        full_name=record["full_name"],
                        role=record["role"],
                        email=record["email"],
                        password_hash=demo_password_hash,
                        is_active=True,
                    )
                    for record in DEMO_USERS
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
                        lat=14.9574,
                        lng=120.9634,
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
                        lat=14.9703,
                        lng=120.9785,
                        notes="Two infants in household",
                    ),
                    Household(
                        household_no="H-003",
                        head_name="Alicia Ramos",
                        address="33 Luna Street",
                        barangay="BMA-Balagtas",
                        size=3,
                        children_count=1,
                        elderly_count=0,
                        pwd_count=0,
                        contact="09170009999",
                        lat=14.9565,
                        lng=120.9524,
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
                        lat=14.9578,
                        lng=120.9642,
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
                        lat=14.9692,
                        lng=120.9788,
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
                        lat=14.9903,
                        lng=120.9625,
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
                        barangay="BMA-Balagtas",
                        severity="high",
                        status="responding",
                        description="Water level rising near the creek after heavy rain.",
                        reported_at="2026-09-24T08:15:00+00:00",
                        updated_at="2026-09-25T09:00:00+00:00",
                        lat=14.9560,
                        lng=120.9530,
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
                        lat=14.9585,
                        lng=120.9660,
                        affected_households=6,
                        reported_by="responder",
                    ),
                ]
            )

        db.commit()
    finally:
        db.close()


def get_households(barangay: str | None = None, params: PageParams | None = None):
    db = SessionLocal()
    try:
        query = db.query(Household)
        if barangay:
            query = query.filter(Household.barangay.ilike(barangay))
        if params is not None:
            query = query.filter(Household.is_active.is_(True))
            query = apply_sort_and_search(
                query,
                Household,
                params,
                searchable=["household_no", "head_name", "address", "barangay", "contact"],
                sortable=HOUSEHOLD_SORTABLE,
            )
            total = query.order_by(None).count()
            rows = query.offset(params.offset).limit(params.page_size).all()
            return build_page(
                [serialize_household(item) for item in rows], total, params, sortable=HOUSEHOLD_SORTABLE
            )
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


def _with_household_coordinates(payload: dict[str, Any]) -> dict[str, Any]:
    """Fill in missing lat/lng from the barangay centroid.

    ``lat``/``lng`` are NOT NULL in the database, and a household registered from
    a form or an import often has no pin dropped yet.
    """
    record = dict(payload)
    lat, lng = record.get("lat"), record.get("lng")
    if lat is None or lng is None:
        fallback_lat, fallback_lng = coordinates_for(record.get("barangay") or "")
        record["lat"] = lat if lat is not None else fallback_lat
        record["lng"] = lng if lng is not None else fallback_lng
    return record


def create_household(payload: dict[str, Any]):
    db = SessionLocal()
    try:
        record = _with_household_coordinates(payload)
        item = Household(**record)
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
            required_fields = ("household_no", "head_name", "address", "barangay")
            if any(not payload[field] for field in required_fields):
                continue
            if not row.get("lat") or not row.get("lng"):
                fallback_lat, fallback_lng = coordinates_for(payload["barangay"])
                payload["lat"] = fallback_lat
                payload["lng"] = fallback_lng
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


def _geometry_to_lat_lng(geometry: dict[str, Any]) -> tuple[float, float] | None:
    """Best-effort representative point for a GeoJSON geometry.

    Uses the centroid where one is computable, otherwise falls back to the first
    coordinate pair. Polygon ring order can shift the centroid slightly outside
    the shape, which is acceptable for a marker.
    """
    if not isinstance(geometry, dict):
        return None
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")

    def flatten(coords) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        if isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (int, float)):
            if len(coords) >= 2:
                points.append((float(coords[0]), float(coords[1])))
        elif isinstance(coords, (list, tuple)):
            for entry in coords:
                points.extend(flatten(entry))
        return points

    if kind == "GeometryCollection":
        for sub in geometry.get("geometries") or []:
            result = _geometry_to_lat_lng(sub)
            if result:
                return result
        return None

    points = flatten(coordinates)
    if not points:
        return None
    # GeoJSON orders coordinates [longitude, latitude]; the rest of the app uses
    # (lat, lng), so swap on the way out.
    lng = sum(point[0] for point in points) / len(points)
    lat = sum(point[1] for point in points) / len(points)
    return (round(lat, 6), round(lng, 6))


def _first_prop(props: dict[str, Any], *names: str, default: Any = "") -> Any:
    """Return the first present, non-empty property among ``names``."""
    for name in names:
        value = props.get(name)
        if value not in (None, ""):
            return value
    return default


def import_households_geojson(payload: dict[str, Any]) -> dict[str, Any]:
    """Import households from a GeoJSON FeatureCollection.

    Each feature may carry a centroid in ``center`` or ``centroid``, its own
    Point geometry, or any polygon to be reduced to a representative point.
    Properties map to household fields, with ``barangay`` required.
    """
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Expected a GeoJSON FeatureCollection with a 'features' array")

    created_items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    skipped = 0
    db = SessionLocal()
    try:
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                errors.append({"index": index, "error": "Feature is not an object"})
                continue
            props = feature.get("properties") or {}
            household_no = str(_first_prop(props, "household_no", "householdNo", "household", "id")).strip()
            head_name = str(_first_prop(props, "head_name", "headName", "head", "name")).strip()
            address = str(_first_prop(props, "address", "location", "street")).strip()
            barangay = str(_first_prop(props, "barangay", "district")).strip()

            missing = [
                field
                for field, value in (
                    ("household_no", household_no),
                    ("head_name", head_name),
                    ("address", address),
                    ("barangay", barangay),
                )
                if not value
            ]
            if missing:
                errors.append({"index": index, "error": f"Missing required field(s): {', '.join(missing)}"})
                continue

            lat = lng = None
            centroid = props.get("center") or props.get("centroid")
            if isinstance(centroid, (list, tuple)) and len(centroid) >= 2:
                # GeoJSON convention: [lng, lat].
                lng, lat = float(centroid[0]), float(centroid[1])
            if lat is None:
                parsed = _geometry_to_lat_lng(feature.get("geometry") or {})
                if parsed:
                    lat, lng = parsed
            if lat is None or lng is None:
                lat, lng = coordinates_for(barangay)

            def as_int(value, fallback=0) -> int:
                try:
                    return int(float(value))
                except (TypeError, ValueError):
                    return fallback

            record = {
                "household_no": household_no,
                "head_name": head_name,
                "address": address,
                "barangay": barangay,
                "size": max(1, as_int(_first_prop(props, "size", "household_size", "members"), 1)),
                "children_count": as_int(_first_prop(props, "children_count", "children")),
                "elderly_count": as_int(_first_prop(props, "elderly_count", "elderly", "senior")),
                "pwd_count": as_int(_first_prop(props, "pwd_count", "pwd")),
                "contact": str(_first_prop(props, "contact", "phone")).strip() or None,
                "lat": lat,
                "lng": lng,
                "notes": str(_first_prop(props, "notes", "remarks")).strip() or None,
            }

            existing = db.query(Household).filter(Household.household_no == household_no).first()
            if existing:
                skipped += 1
                continue
            item = Household(**record)
            db.add(item)
            db.flush()
            created_items.append(serialize_household(item))
        db.commit()
        return {
            "created": len(created_items),
            "skipped": skipped,
            "errors": errors,
            "items": created_items,
        }
    finally:
        db.close()


def get_centers(params: PageParams | None = None):
    db = SessionLocal()
    try:
        query = db.query(EvacuationCenter)
        if params is not None:
            query = apply_sort_and_search(
                query,
                EvacuationCenter,
                params,
                searchable=["name", "barangay", "address", "status"],
                sortable=CENTER_SORTABLE,
            )
            total = query.order_by(None).count()
            rows = query.offset(params.offset).limit(params.page_size).all()
            return build_page(
                [serialize_center(item) for item in rows], total, params, sortable=CENTER_SORTABLE
            )
        return [serialize_center(item) for item in query.order_by(EvacuationCenter.id).all()]
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


def delete_center(center_id: int) -> bool:
    """Delete a center. Blocked while it holds people."""
    db = SessionLocal()
    try:
        item = db.query(EvacuationCenter).filter(EvacuationCenter.id == center_id).first()
        if item is None:
            return False
        if item.current_occupants > 0:
            raise ValueError(
                f"Cannot delete {item.name}: it currently houses {item.current_occupants} people. "
                "Set the occupant count to 0 first."
            )
        db.query(EvacuationAssignment).filter(EvacuationAssignment.center_id == center_id).delete()
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


RESOURCE_TYPE_LABELS = {
    "rice": "Rice",
    "water": "Water",
    "medicine": "Medicine",
    "blankets": "Blankets",
    "hygiene": "Hygiene Kits",
    "canned_goods": "Canned Goods",
    "clothing": "Clothing",
    "mats": "Sleeping Mats",
    "tents": "Tents",
    "other": "Other",
}

# Whitelists of sortable columns, shared by the query builder and the response
# envelope so ``sort`` in the payload always reflects the column actually used.
HOUSEHOLD_SORTABLE = (
    "id",
    "household_no",
    "head_name",
    "barangay",
    "size",
    "children_count",
    "elderly_count",
    "pwd_count",
)
CENTER_SORTABLE = ("id", "name", "barangay", "capacity", "current_occupants", "status")
RESOURCE_SORTABLE = ("id", "name", "type", "quantity_on_hand", "threshold", "updated_at")
INCIDENT_SORTABLE = (
    "id",
    "title",
    "type",
    "barangay",
    "severity",
    "status",
    "reported_at",
    "updated_at",
)


def get_resources(params: PageParams | None = None):
    db = SessionLocal()
    try:
        query = db.query(ResourceItem)
        if params is not None:
            query = apply_sort_and_search(
                query,
                ResourceItem,
                params,
                searchable=["name", "type", "stored_in"],
                sortable=RESOURCE_SORTABLE,
            )
            total = query.order_by(None).count()
            rows = query.offset(params.offset).limit(params.page_size).all()
            return build_page(
                [serialize_resource(item) for item in rows], total, params, sortable=RESOURCE_SORTABLE
            )
        return [serialize_resource(item) for item in query.order_by(ResourceItem.id).all()]
    finally:
        db.close()


def get_resource(resource_id: int):
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        return serialize_resource(item) if item else None
    finally:
        db.close()


def create_resource(payload: dict[str, Any]):
    db = SessionLocal()
    try:
        item = ResourceItem(updated_at=utc_now(), **payload)
        db.add(item)
        db.flush()
        db.add(
            ResourceTransaction(
                resource_id=item.id,
                delta=int(item.quantity_on_hand),
                quantity_after=int(item.quantity_on_hand),
                reason="created",
                note="Initial stock",
                performed_by=payload.get("performed_by"),
                created_at=utc_now_dt(),
            )
        )
        db.commit()
        db.refresh(item)
        return serialize_resource(item)
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


def delete_resource(resource_id: int) -> bool:
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        if item is None:
            return False
        db.query(ResourceTransaction).filter(ResourceTransaction.resource_id == resource_id).delete()
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


def adjust_resource(
    resource_id: int,
    delta: int,
    reason: str | None = None,
    note: str | None = None,
    performed_by: str | None = None,
):
    """Apply a stock delta and record it in the audit ledger.

    The ledger is written in the same transaction as the quantity change, so a
    failure can never leave the two out of sync.
    """
    db = SessionLocal()
    try:
        item = db.query(ResourceItem).filter(ResourceItem.id == resource_id).first()
        if item is None:
            return None
        new_quantity = item.quantity_on_hand + delta
        if new_quantity < 0:
            raise ValueError(f"Cannot remove {abs(delta)} units; only {item.quantity_on_hand} on hand")
        item.quantity_on_hand = new_quantity
        item.updated_at = utc_now()
        db.add(
            ResourceTransaction(
                resource_id=item.id,
                delta=delta,
                quantity_after=new_quantity,
                reason=reason or ("stock-in" if delta > 0 else "stock-out"),
                note=note,
                performed_by=performed_by,
                created_at=utc_now_dt(),
            )
        )
        db.commit()
        db.refresh(item)
        return serialize_resource(item)
    finally:
        db.close()


def get_resource_transactions(resource_id: int, limit: int = 50):
    db = SessionLocal()
    try:
        rows = (
            db.query(ResourceTransaction)
            .filter(ResourceTransaction.resource_id == resource_id)
            .order_by(ResourceTransaction.created_at.desc(), ResourceTransaction.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "resource_id": row.resource_id,
                "delta": row.delta,
                "quantity_after": row.quantity_after,
                "reason": row.reason,
                "note": row.note,
                "performed_by": row.performed_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    finally:
        db.close()


def get_resource_summaries():
    db = SessionLocal()
    try:
        grouped: dict[str, dict[str, Any]] = {}
        for resource in db.query(ResourceItem).all():
            key = resource.type
            if key not in grouped:
                grouped[key] = {
                    "type": key,
                    "label": RESOURCE_TYPE_LABELS.get(key, key.replace("_", " ").title()),
                    "total_on_hand": 0,
                    "total_required": 0,
                    "gap": 0,
                    "low_stock_count": 0,
                    "item_count": 0,
                }
            entry = grouped[key]
            entry["total_on_hand"] += int(resource.quantity_on_hand)
            entry["total_required"] += int(resource.threshold)
            entry["item_count"] += 1
            if resource.quantity_on_hand < resource.threshold:
                entry["low_stock_count"] += 1
        for entry in grouped.values():
            entry["gap"] = entry["total_on_hand"] - entry["total_required"]
        return sorted(grouped.values(), key=lambda entry: entry["type"])
    finally:
        db.close()


def list_incidents(params: PageParams | None = None):
    db = SessionLocal()
    try:
        query = db.query(Incident)
        if params is not None:
            query = apply_sort_and_search(
                query,
                Incident,
                params,
                searchable=["title", "type", "barangay", "status", "severity", "description"],
                sortable=INCIDENT_SORTABLE,
            )
            total = query.order_by(None).count()
            rows = query.offset(params.offset).limit(params.page_size).all()
            return build_page(
                [serialize_incident(item) for item in rows], total, params, sortable=INCIDENT_SORTABLE
            )
        return [serialize_incident(item) for item in query.order_by(Incident.id).all()]
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
        record = dict(payload)
        if isinstance(record.get("zone_geojson"), dict):
            record["zone_geojson"] = json.dumps(record["zone_geojson"])
        now = utc_now()
        item = Incident(reported_at=now, updated_at=now, **record)
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


def update_incident(incident_id: int, payload: dict[str, Any]):
    """Full incident update, not just status."""
    db = SessionLocal()
    try:
        item = db.query(Incident).filter(Incident.id == incident_id).first()
        if item is None:
            return None
        for key, value in payload.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, json.dumps(value) if key == "zone_geojson" and isinstance(value, dict) else value)
        item.updated_at = utc_now()
        db.commit()
        db.refresh(item)
        return serialize_incident(item)
    finally:
        db.close()


def delete_incident(incident_id: int) -> bool:
    db = SessionLocal()
    try:
        item = db.query(Incident).filter(Incident.id == incident_id).first()
        if item is None:
            return False
        db.delete(item)
        db.commit()
        return True
    finally:
        db.close()


def calculate_allocation(
    barangay: str | None = None,
    affected_households: int | None = None,
    persist: bool = False,
):
    """Thin wrapper so existing imports keep working; logic lives in services/allocation."""
    from app.services.allocation import calculate_allocation as _calculate

    return _calculate(barangay=barangay, affected_households=affected_households, persist=persist)


def dashboard_stats():
    db = SessionLocal()
    try:
        households = [
            serialize_household(item) for item in db.query(Household).filter(Household.is_active.is_(True)).all()
        ]
        incidents = [serialize_incident(item) for item in db.query(Incident).all()]
        centers = [serialize_center(item) for item in db.query(EvacuationCenter).all()]
        resources = [serialize_resource(item) for item in db.query(ResourceItem).all()]
    finally:
        db.close()

    vulnerable = sum(item["children_count"] + item["elderly_count"] + item["pwd_count"] for item in households)
    active_incidents = sum(1 for incident in incidents if incident["status"] != "resolved")
    critical_incidents = sum(
        1 for incident in incidents if incident["severity"] == "critical" and incident["status"] != "resolved"
    )
    available_capacity = sum(
        center["capacity"] - center["current_occupants"] for center in centers if center["status"] != "closed"
    )
    low_stock_resources = sum(1 for resource in resources if resource["quantity_on_hand"] < resource["threshold"])
    total_people = sum(item["size"] for item in households)
    return {
        "households": len(households),
        "total_people": total_people,
        "vulnerable_members": vulnerable,
        "active_incidents": active_incidents,
        "critical_incidents": critical_incidents,
        "centers": len(centers),
        "available_capacity": available_capacity,
        "total_capacity": sum(center["capacity"] for center in centers if center["status"] != "closed"),
        "low_stock_resources": low_stock_resources,
    }


def run_scenario(barangay: str, affected_households: int):
    """Model a disaster in one barangay.

    ``affected_households`` caps how many households are at risk; the run then
    works out the real headcount, and relief requirements are computed from
    *people*. The previous version divided by household count, which understated
    need for larger families.
    """
    from app.services.allocation import resource_requirements

    allocation = calculate_allocation(barangay, affected_households=affected_households)
    total_people = allocation.get("assigned_people", 0) + sum(
        item["size"] for item in allocation.get("overflow", [])
    )

    db = SessionLocal()
    try:
        resources = [serialize_resource(item) for item in db.query(ResourceItem).all()]
    finally:
        db.close()

    factors = resource_requirements(total_people)
    resource_needs = []
    for resource in resources:
        factor = factors.get(resource["type"], 0.2)
        required = int(total_people * factor)
        deficit = max(0, required - resource["quantity_on_hand"])
        if deficit == 0:
            status = "adequate"
        elif required == 0 or deficit > required * 0.5:
            status = "critical"
        else:
            status = "shortage"
        resource_needs.append(
            {
                "resource_id": resource["id"],
                "name": resource["name"],
                "type": resource["type"],
                "current": resource["quantity_on_hand"],
                "required": required,
                "deficit": deficit,
                "unit": resource["unit"],
                "status": status,
            }
        )

    return {
        "scenario": {
            "title": f"{barangay} affected ({affected_households} households, {total_people} people)",
            "barangay": barangay,
            "affected_households": affected_households,
            "total_people": total_people,
            "basis": "requirements are calculated per person, not per household",
        },
        "allocation": allocation,
        "resource_needs": resource_needs,
    }

