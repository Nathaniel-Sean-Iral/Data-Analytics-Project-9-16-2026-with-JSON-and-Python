from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.resource import Resource
from app.schemas.schemas import ScenarioReportOut, SimulatorRequest
from app.services.analytics import run_scenario

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/run", response_model=ScenarioReportOut)
def run_simulation(
    body: SimulatorRequest,
    db: Session = Depends(get_db),
    _: Resource = Depends(require_roles("responder", "admin")),
):
    return run_scenario(db, barangay=body.barangay, affected_households=body.affected_households)