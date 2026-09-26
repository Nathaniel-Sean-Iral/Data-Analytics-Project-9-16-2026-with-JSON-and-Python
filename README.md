# Local Disaster Preparedness System

A full-stack disaster operations management platform for a local government unit. It digitizes the municipality's household registry, evacuation centers, relief stock, and incident reporting — then layers **evacuation allocation**, **scenario simulation**, and **live resource analytics** on top of that data.

Built as a monorepo:

| Directory | Stack | Purpose |
| --- | --- | --- |
| `frontend/` | React 18 + TypeScript + Vite, Tailwind CSS, Leaflet, Recharts | Operations dashboard UI |
| `backend/` | FastAPI + SQLAlchemy + SQLite (PostgreSQL-ready), JWT auth | REST API under `/api` |

The two parts are fully wired: the React app talks to the FastAPI backend over HTTP (via the Vite dev proxy), and the backend persists everything to a real database. The frontend has a demo-data fallback so the UI stays browsable even when the API is down.

## Documentation

- [`docs/ERD.md`](docs/ERD.md) — data model, entity diagram, business rules
- [`docs/API.md`](docs/API.md) — endpoint reference, payloads, error codes
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Docker Compose, manual deploy, migrations, config reference
- [`PROGRESS.md`](PROGRESS.md) — live status of all phases/stages

---

## Features

- **Auth & role-based access** — JWT login; three roles: `admin`, `responder`, `viewer`.
  - Reads: all roles · Incidents/allocation/simulator: `responder`+ · Households/centers/resources mutations: `admin`.
- **Household registry** — full CRUD with pagination, search, sorting, and barangay filters. Tracks vulnerable members (children, elderly, PWD).
- **Evacuation centers** — CRUD with capacity, current occupancy, facilities, live status, and map coordinates.
- **Resource stock** — CRUD with stock thresholds, low-stock alerts, and audited stock adjustments (transactions log).
- **Incident reporting** — CRUD with a status workflow (`reported → assessing → responding → resolved`) and severity levels.
- **Analytics dashboard** — aggregate counts, vulnerable-member totals, center capacity, low-stock items.
- **Evacuation allocation engine** — assigns affected households to the nearest center with remaining capacity; reports center load %, overflow, and barangay coverage gaps. Assignments persist.
- **Scenario simulator** — "what-if" runs that project center loads and per-resource shortfalls for a given number of evacuees.
- **Interactive map** — centers, households, and incidents rendered with Leaflet from live API data.

---

## Repository layout

```
disaster-prep-workplan.md   # original project plan & requirements
PROGRESS.md                 # live progress log (updated per stage)
frontend/
  src/
    api/                     # types, HTTP client, services (contract), demo mocks
    pages/                   # Dashboard, Map, Households, Centers, Resources,
                             # Incidents, IncidentDetail, Allocation, Simulator, Login, 404
    components/              # layout shell, UI primitives
    context/                 # auth context (token + user in localStorage)
  vite.config.ts             # dev proxy: /api → http://localhost:8000
backend/
  app/
    main.py                  # FastAPI app, CORS, routers
    core/                    # config, database, security (PBKDF2/JWT), deps (RBAC)
    models/                  # SQLAlchemy models
    schemas/                 # Pydantic request/response schemas
    api/                     # routers: auth, households, centers, resources,
                             # incidents, evacuations, simulator, dashboard, meta
    services/                # allocation, simulator, analytics logic
  seed.py                    # demo data (admin/admin etc.)
  tests/                     # pytest suite (46 tests)
```

---

## Quick start (development)

Prerequisites: **Node ≥ 18**, **Python ≥ 3.11**.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# (optional) seed demo data — 40 households, 6 centers, 8 resources, 5 incidents
.\.venv\Scripts\python seed.py

# run the API
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Demo accounts: `admin/admin` · `responder/responder` · `viewer/viewer`

### 2. Frontend

```powershell
cd frontend
npm install        # first time only (or `npm ci`)
npm run dev        # → http://localhost:5173
```

The Vite dev server proxies `/api/*` to the backend at `http://localhost:8000`.

### 3. Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q        # 46 tests, uses a throwaway SQLite DB
```

---

## Configuration (backend)

Settings are read from environment variables (or a `.env` file next to `backend/`). Full list in `backend/app/core/config.py`:

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./disaster_prep.db` | Use a PostgreSQL DSN in production, e.g. `postgresql+psycopg://user:pass@host/db` |
| `SECRET_KEY` | dev-only string | Change in production; ≥ 32 bytes recommended |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` (8 h) | JWT lifetime |
| `CORS_ORIGINS` | `["*"]` | Comma-separated list in `.env` |

> **Note:** for development the app auto-creates tables on startup (SQLite only). For production you must run migrations — see `docs/DEPLOYMENT.md`. In Docker Compose, `alembic upgrade head` runs automatically before the API starts.

---

## API surface

All endpoints live under `/api` and require a `Bearer` token except login/health. See `backend/app/api/` or `/docs` for the authoritative OpenAPI spec.

| Area | Endpoints |
| --- | --- |
| Auth | `POST /auth/login`, `GET /auth/me` |
| Households | `GET/POST /households`, `GET/PUT/DELETE /households/{id}` |
| Centers | `GET/POST /centers`, `GET/PUT/DELETE /centers/{id}` |
| Resources | `GET /resources`, `GET /resources/summary`, `POST /resources/adjust`, `PATCH /resources/{id}`, `POST /resources/{id}/threshold` |
| Incidents | `GET/POST /incidents`, `GET/PATCH/DELETE /incidents/{id}` (+ status workflow) |
| Evacuations | `POST /evacuations/allocate`, `GET /evacuations/center-loads` |
| Simulator | `POST /simulator/run` |
| Dashboard | `GET /dashboard/stats` |
| Meta | `GET /meta/barangays` |

---

## Status

Core system: **working end-to-end.** Hardening is now in place too — Alembic migrations, Docker Compose, CI (GitHub Actions), and full docs. Remaining niceties tracked in `PROGRESS.md`.