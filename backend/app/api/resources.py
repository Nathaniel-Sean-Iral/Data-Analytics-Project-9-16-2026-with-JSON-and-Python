from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_roles
from app.schemas import Resource, ResourceAdjustment, ResourceCreate
from app.services.pagination import PageParams
from app.services.store import (
    adjust_resource,
    create_resource,
    delete_resource,
    get_resource,
    get_resource_summaries,
    get_resource_transactions,
    get_resources,
    update_resource,
)

router = APIRouter(tags=["resources"])


@router.get("/resources")
def list_resources(
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=200),
    sort: str | None = Query(default=None),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    search: str | None = Query(default=None),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    """Plain list unless pagination, sort, or search is requested."""
    if page is None and page_size is None and sort is None and search is None:
        return get_resources()
    params = PageParams(page=page or 1, page_size=page_size or 25, sort=sort, order=order, search=search)
    return get_resources(params)


@router.get("/resources/summary")
def resource_summary(_user=Depends(require_roles("admin", "responder", "viewer"))):
    return get_resource_summaries()


@router.post("/resources", response_model=Resource, status_code=status.HTTP_201_CREATED)
def add_resource(payload: ResourceCreate, _user=Depends(require_roles("admin", "responder"))):
    return create_resource(payload.model_dump())


@router.post("/resources/adjust")
def adjust_stock(payload: ResourceAdjustment, user=Depends(require_roles("admin", "responder"))):
    try:
        resource = adjust_resource(
            payload.resource_id,
            payload.delta,
            payload.reason,
            note=payload.note,
            performed_by=user.get("username") if isinstance(user, dict) else getattr(user, "username", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.get("/resources/{resource_id}/transactions")
def list_transactions(
    resource_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    if get_resource(resource_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return get_resource_transactions(resource_id, limit=limit)


@router.get("/resources/{resource_id}")
def get_resource_by_id(resource_id: int, _user=Depends(require_roles("admin", "responder", "viewer"))):
    resource = get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.patch("/resources/{resource_id}")
def update_threshold(resource_id: int, payload: dict, _user=Depends(require_roles("admin", "responder"))):
    threshold = payload.get("threshold")
    if threshold is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="threshold is required")
    resource = get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    updated = update_resource(resource_id, {"threshold": threshold, "updated_at": resource["updated_at"]})
    return updated


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_resource(resource_id: int, _user=Depends(require_roles("admin"))):
    if not delete_resource(resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return None
