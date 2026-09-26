from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.resource import Resource, StockTransaction
from app.schemas.schemas import (
    ResourceCreate,
    ResourceOut,
    ResourceSummaryOut,
    ResourceThresholdUpdate,
    ResourceUpdate,
    StockAdjustRequest,
)
from app.services.analytics import resource_summaries

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOut])
def list_resources(
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("viewer", "responder", "admin")),
):
    return db.query(Resource).order_by(Resource.id).all()


@router.get("/summary", response_model=list[ResourceSummaryOut])
def summarize_resources(
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("viewer", "responder", "admin")),
):
    return resource_summaries(db)


@router.get("/{resource_id}", response_model=ResourceOut)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("viewer", "responder", "admin")),
):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
def create_resource(
    body: ResourceCreate,
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("admin")),
):
    resource = Resource(**body.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.patch("/{resource_id}", response_model=ResourceOut)
def update_resource(
    resource_id: int,
    body: ResourceUpdate,
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("admin")),
):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(resource, key, value)
    db.commit()
    db.refresh(resource)
    return resource


@router.post("/adjust", response_model=ResourceOut)
def adjust_stock(
    body: StockAdjustRequest,
    current_user: Resource = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    resource = db.get(Resource, body.resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    new_qty = resource.quantity_on_hand + body.delta
    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot go below zero (current: {resource.quantity_on_hand}, delta: {body.delta})",
        )

    resource.quantity_on_hand = new_qty
    txn = StockTransaction(
        resource_id=resource.id,
        delta=body.delta,
        reason=body.reason,
        created_by=getattr(current_user, "id", None),
    )
    db.add(txn)
    db.commit()
    db.refresh(resource)
    return resource


@router.post("/{resource_id}/threshold", response_model=ResourceOut)
def set_threshold(
    resource_id: int,
    body: ResourceThresholdUpdate,
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("admin")),
):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    resource.threshold = body.threshold
    db.commit()
    db.refresh(resource)
    return resource