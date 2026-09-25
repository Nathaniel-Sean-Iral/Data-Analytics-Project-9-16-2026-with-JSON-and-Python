from fastapi import APIRouter, Depends

from app.core.deps import require_roles
from app.services.store import dashboard_stats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats")
def dashboard_summary(_user=Depends(require_roles("admin", "responder", "viewer"))):
    return dashboard_stats()
