# Deployment Guide

Two supported ways to run the system:

1. **Development** — uvicorn (SQLite) + `npm run dev`, as in the root README.
2. **Production (recommended)** — Docker Compose: Nginx (React static build) + FastAPI + PostgreSQL.

---

## Quick production start (Docker Compose)

Prerequisite: Docker with Compose v2.

```bash
docker compose up --build -d
```

This brings up:

| Service | Image | Notes |
| --- | --- | --- |
| `db` | postgres:16-alpine | named volume `pgdata`; creds `disaster/disaster`, db `disaster_prep` |
| `api` | built from `backend/Dockerfile` | runs `alembic upgrade head` then uvicorn on :8000 |
| `web` | built from `frontend/Dockerfile` | Nginx serving the React build on host :80, proxying `/api` → `api:8000` |

- App: http://localhost
- API docs: http://localhost/docs
- Health: http://localhost/health

### Secrets / config

Override via an `.env` file next to `docker-compose.yml`:

```bash
SECRET_KEY=replace-with-a-long-random-string
```

For a real production DB, replace the `db` service or set `api.environment.DATABASE_URL`

```bash
postgresql+psycopg://user:pass@host:5432/dbname
```

### Seed data (optional)

```bash
docker compose exec api python seed.py
```

Demo accounts: `admin/admin`, `responder/responder`, `viewer/viewer`.

> The seed script is idempotent (skips existing rows) except users are added only if missing; households/centers/resources/incidents are skipped once any rows exist.

---

## Manual production deploy (no Docker)

1. **Database** — provision PostgreSQL, create a database and user.
2. **Backend**
   ```bash
   cd backend
   python -m venv .venv && . .venv/bin/activate   # (or .venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/disaster_prep"
   export SECRET_KEY="a-long-random-secret"
   alembic upgrade head
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. **Frontend**
   ```bash
   cd frontend
   npm ci
   npm run build        # emits dist/
   ```
   Serve `frontend/dist/` from Nginx and proxy `/api` to the backend (see `frontend/nginx.conf` for the exact rules).

---

## Migrations (Alembic)

- Generate a new migration after model changes:
  ```bash
  cd backend
  DATABASE_URL=sqlite:///./empty.db alembic revision --autogenerate -m "describe change"
  ```
- Apply: `alembic upgrade head` · rollback one: `alembic downgrade -1`
- **SQLite dev caveat:** the app auto-creates tables on startup (dev mode), so an existing `disaster_prep.db` predates Alembic. To bring an existing DB under migration control, run `alembic stamp head` once. Fresh databases created via the running dev app are fine as-is; production (Postgres) never auto-creates tables — it only uses `alembic upgrade head`.

---

## Configuration reference

Full list in `backend/app/core/config.py`. Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./disaster_prep.db` | SQLAlchemy URL (SQLite dev, Postgres prod) |
| `SECRET_KEY` | dev-only | JWT signing key — must be changed & kept secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Session lifetime (8 h) |
| `CORS_ORIGINS` | `["*"]` | Allowed origins (JSON list string) |
| `DAYS_WATER_PER_PERSON` | `3.0` | Simulator water rate (gallons) |
| `RICE_SACKS_PER_PERSON` | `0.1` | Simulator rice rate (50 kg sacks) |
| `AVG_PERSONS_PER_HOUSEHOLD` | `4` | Simulator household-to-evacuee multiplier |

---

## Ops notes

- **Backups:** SQLite = copy `backend/disaster_prep.db`; Postgres = `pg_dump`.
- **Logs:** uvicorn logs to stdout (`docker compose logs -f api`).
- **Health check:** `GET /health` → `{"status": "ok"}`.
- **Monitoring hooks:** the only stateful writes beyond CRUD are `stock_transactions` (audit) and `evacuation_assignments` (allocation history) — both are append-only ledger tables.