from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import require_roles
from app.services.allocation import get_assignment_run
from app.services.store import calculate_allocation

router = APIRouter(tags=["evacuations"])


class AllocationRequest(BaseModel):
    barangay: str | None = None
    affected_households: int | None = Field(default=None, ge=1)
    persist: bool = False


@router.post("/evacuations/allocate")
def allocate_households(
    payload: AllocationRequest | None = None,
    _user=Depends(require_roles("admin", "responder")),
):
    """Assign households to centers, counting occupancy in people rather than
    households. Set ``persist`` to write the run to ``evacuation_assignments``.
    """
    request = payload or AllocationRequest()
    return calculate_allocation(
        request.barangay,
        affected_households=request.affected_households,
        persist=request.persist,
    )


@router.get("/evacuations/center-loads")
def center_loads(_user=Depends(require_roles("admin", "responder", "viewer"))):
    result = calculate_allocation()
    return result["center_loads"]


@router.get("/evacuations/assignments/{request_id}")
def assignment_run(request_id: str, _user=Depends(require_roles("admin", "responder", "viewer"))):
    rows = get_assignment_run(request_id)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No allocation run with that id")
    return {"request_id": request_id, "count": len(rows), "assignments": rows}
