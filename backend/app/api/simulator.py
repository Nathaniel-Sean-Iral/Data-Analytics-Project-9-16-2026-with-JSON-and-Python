from fastapi import APIRouter, HTTPException

from app.services.store import run_scenario

router = APIRouter(tags=["simulator"])


@router.post("/simulator/run")
def run_simulator(payload: dict):
    barangay = payload.get("barangay")
    affected_households = payload.get("affected_households")
    if not barangay or affected_households is None:
        raise HTTPException(status_code=400, detail="barangay and affected_households are required")
    return run_scenario(barangay, int(affected_households))
