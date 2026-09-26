from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.center import EvacuationCenter
from app.schemas.schemas import CenterCreate, CenterOut, CenterUpdate

router = APIRouter(prefix="/centers", tags=["centers"])


@router.get("", response_model=list[CenterOut])
def list_centers(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: EvacuationCenter = Depends(require_roles("viewer", "responder", "admin")),
):
    query = db.query(EvacuationCenter)
    if status_filter:
        query = query.filter(EvacuationCenter.status == status_filter)
    return query.order_by(EvacuationCenter.id).all()


@router.get("/{center_id}", response_model=CenterOut)
def get_center(
    center_id: int,
    db: Session = Depends(get_db),
    _: EvacuationCenter = Depends(require_roles("viewer", "responder", "admin")),
):
    center = db.get(EvacuationCenter, center_id)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evacuation center not found")
    return center


@router.post("", response_model=CenterOut, status_code=status.HTTP_201_CREATED)
def create_center(
    body: CenterCreate,
    db: Session = Depends(get_db),
    _: EvacuationCenter = Depends(require_roles("admin")),
):
    center = EvacuationCenter(**body.model_dump())
    db.add(center)
    db.commit()
    db.refresh(center)
    return center


@router.put("/{center_id}", response_model=CenterOut)
def update_center(
    center_id: int,
    body: CenterUpdate,
    db: Session = Depends(get_db),
    _: EvacuationCenter = Depends(require_roles("admin")),
):
    center = db.get(EvacuationCenter, center_id)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evacuation center not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(center, key, value)
    db.commit()
    db.refresh(center)
    return center


@router.delete("/{center_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_center(
    center_id: int,
    db: Session = Depends(get_db),
    _: EvacuationCenter = Depends(require_roles("admin")),
):
    center = db.get(EvacuationCenter, center_id)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evacuation center not found")
    db.delete(center)
    db.commit()