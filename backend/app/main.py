import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.api.auth import router as auth_router
from app.api.centers import router as centers_router
from app.api.dashboard import router as dashboard_router
from app.api.evacuations import router as evacuations_router
from app.api.health import router as health_router
from app.api.households import router as households_router
from app.api.incidents import router as incidents_router
from app.api.resources import router as resources_router
from app.api.simulator import router as simulator_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import *  # noqa: F401,F403
from app.services.store import seed_demo_data

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)


def initialize_database() -> None:
    last_error: Exception | None = None
    for attempt in range(1, 61):
        try:
            Base.metadata.create_all(bind=engine)
            seed_demo_data()
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == 60:
                raise
            time.sleep(2)
    if last_error is not None:
        raise last_error


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(households_router, prefix=settings.API_PREFIX)
app.include_router(centers_router, prefix=settings.API_PREFIX)
app.include_router(resources_router, prefix=settings.API_PREFIX)
app.include_router(incidents_router, prefix=settings.API_PREFIX)
app.include_router(evacuations_router, prefix=settings.API_PREFIX)
app.include_router(simulator_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {"message": "Disaster preparedness API is running."}
