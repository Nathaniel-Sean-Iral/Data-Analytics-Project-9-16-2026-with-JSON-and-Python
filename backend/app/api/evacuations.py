from fastapi import APIRouter, HTTPException, Query

from app.services.store import calculate_allocation

router = APIRouter(tags=["evacuations"])


@router.post("/evacuations/allocate")
def allocate_households(barangay: str | None = Query(default=None), payload: dict | None = None):
    selected_barangay = payload.get("barangay") if payload else barangay
    return calculate_allocation(selected_barangay)


@router.get("/evacuations/center-loads")
def center_loads():
    result = calculate_allocation()
    return result["center_loads"]
