from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.evacuation import EvacuationAssignment
from app.schemas.schemas import AllocationRequest, AllocationResultOut, CenterLoadOut
from app.services.allocation import allocate, center_loads

router = APIRouter(prefix="/evacuations", tags=["evacuations"])


@router.post("/allocate", response_model=AllocationResultOut)
def run_allocation(
    body: AllocationRequest,
    db: Session = Depends(get_db),
    _: EvacuationAssignment = Depends(require_roles("responder", "admin")),
):
    return allocate(db, barangay=body.barangay)


@router.get("/center-loads", response_model=list[CenterLoadOut])
def get_center_loads(
    db: Session = Depends(get_db),
    _: EvacuationAssignment = Depends(require_roles("viewer", "responder", "admin")),
):
    return center_loads(db)