# Local Disaster Preparedness System — San Rafael, Bulacan

This project is a full-stack disaster preparedness dashboard for local officials and responders. It includes household records, evacuation centers, resource tracking, incident reporting, allocation planning, and scenario simulation.

The system is scoped to the **Municipality of San Rafael, Bulacan** (PSGC `031422000`), covering all 34 barangays. Geographic reference data lives in a single place so the API, the seed data, and the map all agree:

| Where | What |
|---|---|
| `backend/app/core/location.py` | Municipality center, bounds, barangay centroids |
| `backend/app/core/barangays.py` | The 34 barangay names |
| `GET /api/location` | Serves the above to any client |
| `frontend/src/lib/location.ts` | Frontend mirror, used for the map's default viewport |

Municipal center (Poblacion): `14.9571, 120.9629`.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite by default
- Frontend: React + TypeScript + Vite + Tailwind
- Maps: MapLibre / OpenStreetMap basemap
- Data model: households, centers, resources, incidents, allocation reports

## Quick start

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app is available at:

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health
- Location metadata: http://localhost:8000/api/location

### 2) Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open:

- http://localhost:5173

## Demo accounts

The seeded accounts are:

- admin / password
- responder / password
- viewer / password

## Project status

This repo already includes the core MVP structure for:

- auth + RBAC
- households CRUD
- centers CRUD
- resources CRUD
- incidents CRUD
- allocations and simulation
- dashboard and map pages
- San Rafael, Bulacan geographic reference data

The app is designed to be demo-ready for local operations planning and internal reviews.

> **Known gap:** the auth layer is still a stand-in. Passwords are compared against a
> hardcoded value and the bearer token is a forgeable string, so it is not real
> authentication yet. See "Next up" below.

## Tests

```bash
cd backend
pytest -q
```

Tests run against a throwaway SQLite database in the system temp directory, so they
never touch your local `disaster_prep.db`. A `conftest.py` creates the schema and
seeds demo data before the suite runs, which is why a fresh checkout needs no setup.

## Environment variables

Create a `.env` file in the backend root if needed:

```env
DATABASE_URL=sqlite:///./disaster_prep.db
API_PREFIX=/api
```

The database file is git-ignored and re-created with demo data on first run.

## Docker

```bash
docker compose up --build
```

This runs the backend, frontend, and Postgres service together.
