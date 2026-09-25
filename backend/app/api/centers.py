from fastapi import APIRouter, HTTPException, status

from app.schemas import CenterCreate, CenterUpdate, EvacuationCenter
from app.services.store import create_center, get_center, get_centers, update_center

router = APIRouter(tags=["centers"])


@router.get("/centers")
def list_centers():
    return get_centers()


@router.get("/centers/{center_id}")
def get_center_by_id(center_id: int):
    center = get_center(center_id)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return center


@router.post("/centers", response_model=EvacuationCenter)
def create_new_center(payload: CenterCreate):
    return create_center(payload.model_dump())


@router.put("/centers/{center_id}", response_model=EvacuationCenter)
def update_existing_center(center_id: int, payload: CenterUpdate):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    center = update_center(center_id, updates)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return center
