from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_roles
from app.schemas import Incident, IncidentCreate, IncidentStatusUpdate
from app.services.store import create_incident, get_incident, list_incidents, update_incident_status

router = APIRouter(tags=["incidents"])


@router.get("/incidents")
def list_all_incidents(_user=Depends(require_roles("admin", "responder", "viewer"))):
    return list_incidents()


@router.get("/incidents/{incident_id}")
def get_incident_by_id(incident_id: int, _user=Depends(require_roles("admin", "responder", "viewer"))):
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/incidents", response_model=Incident)
def create_new_incident(payload: IncidentCreate, _user=Depends(require_roles("admin", "responder"))):
    return create_incident(payload.model_dump())


@router.patch("/incidents/{incident_id}", response_model=Incident)
def update_status(incident_id: int, payload: IncidentStatusUpdate, _user=Depends(require_roles("admin", "responder"))):
    incident = update_incident_status(incident_id, payload.status)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident
