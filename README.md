# Local Disaster Preparedness System — San Rafael, Bulacan

A full-stack disaster preparedness and evacuation planning dashboard for local
officials and responders. It tracks household records, evacuation centers,
relief resources, and incidents, then turns them into allocation plans and
scenario simulations for the whole municipality.

**What it does**

| Area | Capability |
|---|---|
| Households | Registry with vulnerable-member counts, GeoJSON/CSV import, map markers |
| Centers | Evacuation centers with capacity, occupants, facilities, status |
| Resources | Stock by type with thresholds, low-stock alerts, adjustment ledger |
| Incidents | Reporting with severity/status workflow and GeoJSON impact zones |
| Allocation | Nearest-center assignment by people, no household splitting, persisted runs |
| Simulator | Scenario planning: pick a barangay and resource mix, see requirements vs. supply |
| Dashboard | Municipality-wide stats, capacity, vulnerable counts, incident summary |
| Auth | JWT login/refresh with `admin` / `responder` / `viewer` roles |

The system is scoped to the **Municipality of San Rafael, Bulacan** (PSGC `031422000`), covering all 34 barangays. Geographic reference data lives in a single place so the API, the seed data, and the map all agree:

| Where | What |
|---|---|
| `backend/app/core/location.py` | Municipality center, bounds, barangay centroids |
| `backend/app/core/barangays.py` | The 34 barangay names |
| `GET /api/location` | Serves the above to any client |
| `frontend/src/lib/location.ts` | Frontend mirror, used for the map's default viewport |

Municipal center (Poblacion): `14.9571, 120.9629`.

All bundled data is fabricated sample data for demonstration purposes only — it
is not a census extract or an official DRRM record.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite by default (Postgres supported)
- Auth: JWT access + refresh tokens, password hashing, role-based access
- Schema: Alembic migrations
- Frontend: React + TypeScript + Vite + Tailwind
- Maps: MapLibre / OpenStreetMap basemap
- Data model: households, centers, resources, incidents, allocation reports

## Quick start

Prerequisites: Python 3.12+ and Node 20+ (the versions CI uses).

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start the app creates the SQLite database, applies the schema, and
seeds the demo dataset — nothing else to run.

The app is available at:

- API: http://localhost:8000
- Health check: http://localhost:8000/api/health
- Interactive docs: http://localhost:8000/docs
- Location metadata: http://localhost:8000/api/location

### 2) Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open:

- http://localhost:5173

The Vite dev server proxies `/api` to the backend, so log in from the UI.

### Startup order

The backend must be running before the frontend is useful (every page needs
data). If the port is busy, stop the other process first — a stale server on
`8000` will answer with 401s that look like bad credentials.

## Demo accounts

| Role | Username | Password | Can do |
|---|---|---|---|
| Administrator | `admin` | `password` | Everything, including deleting records and managing users |
| Responder | `responder` | `password` | Create and update records, run allocations, adjust stock |
| Read-only | `viewer` | `password` | Browse the dashboard, map, and lists; no writes |

## Demo dataset

A fresh database seeds ~240 households across all 34 barangays, 9 evacuation
centers, 8 resource types (4 below threshold, to exercise low-stock alerts), and
3 incidents with GeoJSON zones drawn on the map.

Import samples live in `sample-data/`:

| File | Endpoint |
|---|---|
| `households_import_test.csv` | `POST /api/households/import` — 30 rows with fresh IDs, reports "30 created" |
| `households_san_rafael.csv` | `POST /api/households/import` — full 240 rows, dedupes against a seeded DB |
| `households_san_rafael.geojson` | `POST /api/households/import/geojson` |

The import endpoint skips rows whose `household_no` already exists, so use
`households_import_test.csv` to see rows actually created. Only CSV and GeoJSON
are accepted; `.xlsx` is not.

Regenerate the samples with:

```bash
cd backend
python -m scripts.generate_sample_data
```

## Project status

Implemented and tested:

- JWT auth + refresh, role-based access control
- Households, centers, resources, incidents CRUD at the API level
- CSV + GeoJSON household import with dedupe
- Resource adjustment ledger and low-stock alerting
- Allocation engine and scenario simulator
- Dashboard stats, map layers (households, centers, incident zones)
- Alembic migrations, deterministic demo seed, Docker/Nginx deployment files

Not done yet:

- UI for creating/deleting resources, deleting centers, and editing/deleting incidents
- Frontend test suite (backend has 108 tests)
- Excel `.xlsx` import
- The production compose stack has not been built and run on this machine

## Tests

```bash
cd backend
pytest -q          # 108 tests
ruff check .
alembic check      # verifies models and migrations agree
```

Tests run against a throwaway SQLite database in the system temp directory, so they
never touch your local `disaster_prep.db`. A `conftest.py` creates the schema and
seeds demo data before the suite runs, which is why a fresh checkout needs no setup.
CI (`.github/workflows/ci.yml`) runs the same three checks plus `npm run build`.

## Environment variables

Copy `.env.example` to `backend/.env` to override defaults:

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./disaster_prep.db` | Postgres URLs supported |
| `API_PREFIX` | `/api` | Route prefix for all endpoints |
| `SECRET_KEY` | dev fallback | **Required outside development** |
| `SEED_DEMO_DATA` | `true` in dev | Seeds users and the demo dataset |
| `DEMO_PASSWORD` | `password` | Password for all demo accounts |
| `CORS_ORIGINS` | dev origins | JSON list of allowed origins |
| `HTTP_PORT` | `80` | Production compose host port |

Generate a production key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The database file is git-ignored and re-created with demo data on first run.

## Database migrations

A fresh clone needs no migration step (`create_all` + seeds run on startup). For
an existing database after a schema change:

```bash
cd backend
alembic upgrade head
```

## Docker

Development stack (backend + frontend + Postgres):

```bash
docker compose up --build
```

Production stack (nginx-served frontend, API behind `/api`, Postgres on an
internal network) is documented in [DEPLOYMENT.md](DEPLOYMENT.md):

```bash
cp .env.example .env      # then set SECRET_KEY
docker compose -f docker-compose.prod.yml up --build -d
```

To wipe and re-seed for a clean demo, stop the server and delete
`backend/disaster_prep.db`; see [DEPLOYMENT.md](DEPLOYMENT.md#demo-dataset).

