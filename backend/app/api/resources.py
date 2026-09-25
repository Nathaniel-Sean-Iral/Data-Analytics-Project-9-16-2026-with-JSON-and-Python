from fastapi import APIRouter, HTTPException, status

from app.schemas import Resource, ResourceAdjustment, ResourceSummary
from app.services.store import adjust_resource, get_resource, get_resource_summaries, get_resources, update_resource

router = APIRouter(tags=["resources"])


@router.get("/resources")
def list_resources():
    return get_resources()


@router.get("/resources/summary")
def resource_summary():
    return get_resource_summaries()


@router.post("/resources/adjust")
def adjust_stock(payload: ResourceAdjustment):
    resource = adjust_resource(payload.resource_id, payload.delta, payload.reason)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.patch("/resources/{resource_id}")
def update_threshold(resource_id: int, payload: dict):
    threshold = payload.get("threshold")
    if threshold is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="threshold is required")
    resource = get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    updated = update_resource(resource_id, {"threshold": threshold, "updated_at": resource["updated_at"]})
    return updated
