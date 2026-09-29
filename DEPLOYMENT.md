# Deployment Guide

Two ways to run the San Rafael disaster preparedness system.

## Option A — Dev on bare metal (quickest)

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload                    # http://localhost:8000/api

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                                      # http://localhost:5173
```

The backend defaults to a SQLite file and seeds demo data. Set `SECRET_KEY`
outside development when not running with the default dev settings:

```powershell
$env:SECRET_KEY = "<generated>"
```

Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Option B — Docker Compose

### Dev stack (Vite dev server + FastAPI + PostgreSQL)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- `db` uses `network_mode: host` on the local machine, so **it requires Linux**.
  On Windows/macOS prefer a WSL2 context or the production stack with a
  PostgreSQL service you control.

### Production stack (Nginx serving the React build)

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY, DEMO_PASSWORD, POSTGRES_PASSWORD, HTTP_PORT.

docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

- App: http://localhost:80 (or `${HTTP_PORT}`)
- API on the same origin under `/api` — no CORS in production.
- Docs: http://localhost/api/docs

How the production frontend works:

1. `frontend/Dockerfile.prod` is a multi-stage build: Node builds `dist` with
   `VITE_API_URL=/api`, then Nginx images that output.
2. `frontend/nginx.conf` serves the SPA (`try_files ... /index.html`), caches
   fingerprinted `/assets/` for a year, and proxies `/api` to `backend:8000`.
3. `docker-compose.prod.yml` removes the backend/dev frontend host ports, runs
   PostgreSQL on the compose network, and wires an `envsubst`-less `.env`
   through Compose variable interpolation.

### After first boot

Demo accounts (`SEED_DEMO_DATA=true`) log in as `admin`, `responder`, or
`viewer` with `DEMO_PASSWORD`. Disable demo seeding and rotate the password
before real use.

### Demo dataset

A first boot seeds a deterministic, demo-only San Rafael dataset: ~240
households across all 34 barangays, 9 evacuation centers, 8 resource types
(four below threshold, to exercise low-stock alerts), and 3 incidents with
GeoJSON zones on the map. It is fabricated sample data, not a census extract.

To wipe and re-seed for a clean demo, delete the database and restart the API:

```powershell
Stop-Process -Name python -Force   # the uvicorn holding the file
Remove-Item backend\disaster_prep.db
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Sample files for the import flow (regenerate with
`backend\python -m scripts.generate_sample_data`):

- `sample-data/households_san_rafael.csv` → `POST /api/households/import` (Households page)
- `sample-data/households_san_rafael.geojson` → `POST /api/households/import/geojson`

Importing the sample files into a freshly seeded DB is idempotent: rows already
in the DB are skipped by `household_no` dedupe.

## Migrations

On a fresh clone `create_all` + seeds run automatically. For schema changes:

```bash
cd backend
alembic upgrade head          # idempotent, run at deploy time for existing DBs
alembic check                 # fail CI if models and migrations diverge
```

Run `alembic upgrade head` against the production database before starting the
backend against it, or the app will create only missing tables via `create_all`
and leave column changes unapplied.

## Backups

On PostgreSQL the entire dataset lives in the `disaster_prep_postgres_data`
volume; back up with `pg_dump` from the `db` container:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  exec db pg_dump -U postgres disaster_prep > backup_$(date +%F).sql
```