from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.household import Household
from app.schemas.schemas import DashboardStatsOut
from app.services.analytics import dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsOut)
def stats(
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("viewer", "responder", "admin")),
):
    return dashboard_stats(db)