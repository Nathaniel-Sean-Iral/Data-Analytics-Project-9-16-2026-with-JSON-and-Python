from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_roles
from app.schemas import Incident, IncidentCreate, IncidentStatusUpdate, IncidentUpdate
from app.services.pagination import PageParams
from app.services.store import (
    create_incident,
    delete_incident,
    get_incident,
    list_incidents,
    update_incident,
    update_incident_status,
)

router = APIRouter(tags=["incidents"])


@router.get("/incidents")
def list_all_incidents(
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=200),
    sort: str | None = Query(default=None),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    search: str | None = Query(default=None),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    """Plain list unless pagination, sort, or search is requested."""
    if page is None and page_size is None and sort is None and search is None:
        return list_incidents()
    params = PageParams(page=page or 1, page_size=page_size or 25, sort=sort, order=order, search=search)
    return list_incidents(params)


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
def patch_incident(
    incident_id: int,
    payload: IncidentUpdate,
    _user=Depends(require_roles("admin", "responder")),
):
    """Partial update of any incident field, including status."""
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    incident = update_incident(incident_id, updates)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.put("/incidents/{incident_id}/status", response_model=Incident)
def update_status(incident_id: int, payload: IncidentStatusUpdate, _user=Depends(require_roles("admin", "responder"))):
    incident = update_incident_status(incident_id, payload.status)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.delete("/incidents/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_incident(incident_id: int, _user=Depends(require_roles("admin"))):
    if not delete_incident(incident_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return None
