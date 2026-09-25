from fastapi import APIRouter

from app.services.store import dashboard_stats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats")
def dashboard_summary():
    return dashboard_stats()
