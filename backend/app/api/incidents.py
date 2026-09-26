from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.incident import Incident
from app.schemas.schemas import (
    IncidentCreate,
    IncidentOut,
    IncidentStatusUpdate,
    IncidentUpdate,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])

VALID_TRANSITIONS = {
    "reported": {"assessing", "responding"},
    "assessing": {"responding", "resolved"},
    "responding": {"resolved"},
    "resolved": {"assessing"},
}


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
    type_filter: str | None = Query(None, alias="type"),
    barangay: str | None = Query(None),
    db: Session = Depends(get_db),
    _: Incident = Depends(require_roles("viewer", "responder", "admin")),
):
    query = db.query(Incident)
    if status_filter:
        query = query.filter(Incident.status == status_filter)
    if severity:
        query = query.filter(Incident.severity == severity)
    if type_filter:
        query = query.filter(Incident.type == type_filter)
    if barangay:
        query = query.filter(Incident.barangay == barangay)
    return query.order_by(Incident.reported_at.desc()).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: Incident = Depends(require_roles("viewer", "responder", "admin")),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    body: IncidentCreate,
    current_user: Incident = Depends(require_roles("responder", "admin")),
    db: Session = Depends(get_db),
):
    incident = Incident(**body.model_dump())
    incident.status = "reported"
    incident.reported_by = getattr(current_user, "full_name", None) or getattr(current_user, "username", None)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int,
    body: IncidentUpdate,
    current_user: Incident = Depends(require_roles("responder", "admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    payload = body.model_dump(exclude_unset=True)
    if "status" in payload and payload["status"] != incident.status:
        allowed = VALID_TRANSITIONS.get(incident.status, set())
        if payload["status"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from '{incident.status}' to '{payload['status']}'",
            )
    for key, value in payload.items():
        setattr(incident, key, value)
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def update_incident_status(
    incident_id: int,
    body: IncidentStatusUpdate,
    current_user: Incident = Depends(require_roles("responder", "admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    allowed = VALID_TRANSITIONS.get(incident.status, set())
    if body.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{incident.status}' to '{body.status}'",
        )
    incident.status = body.status
    incident.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: Incident = Depends(require_roles("admin")),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    db.delete(incident)
    db.commit()