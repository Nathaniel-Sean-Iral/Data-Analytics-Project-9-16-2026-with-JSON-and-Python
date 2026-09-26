from fastapi import APIRouter, Depends

from app.core.deps import require_roles
from app.models.household import Household
from app.services.common import BARANGAYS

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/barangays", response_model=list[str])
def barangays(_: Household = Depends(require_roles("viewer", "responder", "admin"))):
    return BARANGAYS