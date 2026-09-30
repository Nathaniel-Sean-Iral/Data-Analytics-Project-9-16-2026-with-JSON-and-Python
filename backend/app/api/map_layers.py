from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_roles
from app.core.location import MUNICIPALITY_BOUNDS, MUNICIPALITY_CENTER
from app.db.session import SessionLocal
from app.models.center import EvacuationCenter
from app.models.household import Household
from app.models.incident import Incident
from app.schemas import IncidentZoneSave

router = APIRouter(tags=["map"])


def _point(lat: float | None, lng: float | None) -> dict[str, float] | None:
    if lat is None or lng is None:
        return None
    return {"lat": lat, "lng": lng}


@router.get("/map/layers")
def map_layers(
    layer: str = Query(..., pattern="^(households|centers|incidents|zones)$"),
    barangay: str | None = Query(default=None),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    """One GeoJSON FeatureCollection per map layer.

    Kept as separate calls so the client can toggle layers without refetching
    everything, and so a large household layer does not slow the critical ones.
    """
    db = SessionLocal()
    try:
        features: list[dict] = []

        if layer == "households":
            query = db.query(Household).filter(Household.is_active.is_(True))
            if barangay:
                query = query.filter(Household.barangay == barangay)
            for row in query.all():
                position = _point(row.lat, row.lng)
                if position is None:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [position["lng"], position["lat"]]},
                        "properties": {
                            "id": row.id,
                            "household_no": row.household_no,
                            "head_name": row.head_name,
                            "barangay": row.barangay,
                            "size": row.size,
                            "vulnerable": (row.children_count or 0) + (row.elderly_count or 0) + (row.pwd_count or 0),
                        },
                    }
                )

        elif layer == "centers":
            query = db.query(EvacuationCenter)
            if barangay:
                query = query.filter(EvacuationCenter.barangay == barangay)
            for row in query.all():
                position = _point(row.lat, row.lng)
                if position is None:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [position["lng"], position["lat"]]},
                        "properties": {
                            "id": row.id,
                            "name": row.name,
                            "barangay": row.barangay,
                            "capacity": row.capacity,
                            "current_occupants": row.current_occupants,
                            "status": row.status,
                            "load_percent": int((row.current_occupants / row.capacity) * 100)
                            if row.capacity
                            else 0,
                        },
                    }
                )

        elif layer == "incidents":
            query = db.query(Incident)
            if barangay:
                query = query.filter(Incident.barangay == barangay)
            for row in query.all():
                position = _point(row.lat, row.lng)
                if position is None:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [position["lng"], position["lat"]]},
                        "properties": {
                            "id": row.id,
                            "title": row.title,
                            "type": row.type,
                            "barangay": row.barangay,
                            "severity": row.severity,
                            "status": row.status,
                        },
                    }
                )

        elif layer == "zones":
            # Only incidents with stored zone geometry produce a polygon.
            query = db.query(Incident).filter(Incident.zone_geojson.isnot(None))
            if barangay:
                query = query.filter(Incident.barangay == barangay)
            for row in query.all():
                import json

                try:
                    geometry = json.loads(row.zone_geojson)
                except (TypeError, ValueError):
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "id": row.id,
                            "title": row.title,
                            "type": row.type,
                            "barangay": row.barangay,
                            "severity": row.severity,
                            "status": row.status,
                        },
                    }
                )
    finally:
        db.close()

    return {
        "type": "FeatureCollection",
        "layer": layer,
        "barangay": barangay,
        "center": {"lat": MUNICIPALITY_CENTER[0], "lng": MUNICIPALITY_CENTER[1]},
        "bounds": MUNICIPALITY_BOUNDS,
        "features": features,
    }


@router.post("/map/zones")
def save_incident_zone(
    payload: IncidentZoneSave,
    _user=Depends(require_roles("admin", "responder")),
):
    """Attach a GeoJSON polygon to an incident."""
    from app.services.store import update_incident

    incident = update_incident(payload.incident_id, {"zone_geojson": payload.geometry})
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident
