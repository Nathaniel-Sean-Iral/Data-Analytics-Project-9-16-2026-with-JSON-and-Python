import time
from contextlib import asynccontextmanager

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
from app.api.location import router as location_router
from app.api.map_layers import router as map_router
from app.api.resources import router as resources_router
from app.api.simulator import router as simulator_router
from app.core.config import settings
from app.core.location import location_label
from app.db.base import Base
from app.db.session import engine
from app.models import *  # noqa: F401,F403
from app.services.store import seed_demo_data

DB_STARTUP_ATTEMPTS = 30
DB_STARTUP_BACKOFF_SECONDS = 2


def initialize_database() -> None:
    last_error: Exception | None = None
    for attempt in range(1, DB_STARTUP_ATTEMPTS + 1):
        try:
            Base.metadata.create_all(bind=engine)
            if settings.SEED_DEMO_DATA:
                seed_demo_data()
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == DB_STARTUP_ATTEMPTS:
                raise
            time.sleep(DB_STARTUP_BACKOFF_SECONDS)
    if last_error is not None:
        raise last_error


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
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
app.include_router(location_router, prefix=settings.API_PREFIX)
app.include_router(map_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "message": "Disaster preparedness API is running.",
        "municipality": location_label(),
        "version": settings.APP_VERSION,
    }
