from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_roles
from app.schemas import Household, HouseholdCreate, HouseholdUpdate
from app.services.store import create_household, delete_household, get_household, get_households, update_household

router = APIRouter(tags=["households"])


@router.get("/households")
def list_households(
    barangay: str | None = Query(default=None),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    items = get_households(barangay)
    return {"items": items, "total": len(items), "page": 1, "page_size": len(items)}


@router.get("/households/{household_id}")
def get_household_by_id(
    household_id: int,
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    household = get_household(household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    return household


@router.post("/households", response_model=Household)
def create_new_household(
    payload: HouseholdCreate,
    _user=Depends(require_roles("admin", "responder")),
):
    return create_household(payload.model_dump())


@router.put("/households/{household_id}", response_model=Household)
def update_existing_household(
    household_id: int,
    payload: HouseholdUpdate,
    _user=Depends(require_roles("admin", "responder")),
):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    household = update_household(household_id, updates)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    return household


@router.delete("/households/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_household(
    household_id: int,
    _user=Depends(require_roles("admin")),
):
    deleted = delete_household(household_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    return None
