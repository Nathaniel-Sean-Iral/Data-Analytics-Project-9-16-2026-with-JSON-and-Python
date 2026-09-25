from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import require_roles
from app.services.store import calculate_allocation

router = APIRouter(tags=["evacuations"])


@router.post("/evacuations/allocate")
def allocate_households(
    barangay: str | None = Query(default=None),
    payload: dict | None = None,
    _user=Depends(require_roles("admin", "responder")),
):
    selected_barangay = payload.get("barangay") if payload else barangay
    return calculate_allocation(selected_barangay)


@router.get("/evacuations/center-loads")
def center_loads(_user=Depends(require_roles("admin", "responder", "viewer"))):
    result = calculate_allocation()
    return result["center_loads"]
