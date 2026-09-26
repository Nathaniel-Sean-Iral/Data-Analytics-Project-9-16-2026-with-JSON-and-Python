from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, centers, dashboard, evacuations, households, incidents, meta, resources, simulator
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Dev convenience: create tables on startup for SQLite only. For any other
    # database (i.e. PostgreSQL) schema is managed by Alembic migrations
    # (`alembic upgrade head`), which run before the app starts in production.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Disaster Preparedness API",
    description="Backend API for the Local Disaster Preparedness System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(households.router, prefix=API_PREFIX)
app.include_router(centers.router, prefix=API_PREFIX)
app.include_router(resources.router, prefix=API_PREFIX)
app.include_router(incidents.router, prefix=API_PREFIX)
app.include_router(evacuations.router, prefix=API_PREFIX)
app.include_router(simulator.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(meta.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {
        "service": "disaster-prep-api",
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {"status": "ok"}