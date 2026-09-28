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

### SECRET_KEY is generated for you

There is no secret to set up front. On first start `backend/entrypoint.sh` generates
a 48-byte random key and persists it to the `api_secret` volume, so restarting the
stack does not invalidate issued tokens. Log in with `admin` / `admin` straight away.

To supply your own key instead, set it in an `.env` file next to `docker-compose.yml`
(see `.env.example`):

```bash
SECRET_KEY=replace-with-a-long-random-string
```

A value that still looks like a placeholder (`change-me`, `dev-only`, under 32
characters) is reported and replaced rather than used. The API also refuses to start
at all if a placeholder reaches it by any other route, so the stack can never end up
signing tokens with a publicly known key.

Losing the `api_secret` volume (`docker compose down -v`) invalidates every issued
token and generates a fresh key.

### Seed data

Seeding is on by default. The API container runs `python seed.py` on startup, and
since the script is idempotent it is a no-op on every restart after the first.

To start with an empty database instead:

```bash
SEED_DEMO_DATA=false docker compose up --build -d
```

Demo accounts: `admin/admin`, `responder/responder`, `viewer/viewer`.

> The seed script is idempotent: users are added only if missing, and
> households/centers/resources/incidents are skipped once any rows exist.

### Database

The schema is owned by Alembic, so `alembic upgrade head` runs automatically on every
API start. Never edit the Postgres tables by hand; add a migration instead.

For a real production DB, replace the `db` service or set `api.environment.DATABASE_URL`:

```bash
postgresql+psycopg://user:pass@host:5432/dbname
```

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
- **Verified:** the initial migration has been applied to a real PostgreSQL 16 container via `docker compose up --build`, and the app was exercised through Nginx against it (login, dashboard, simulator). `alembic check` reports no drift between the models and the migration.

---

## Configuration reference

Full list in `backend/app/core/config.py`. Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./disaster_prep.db` | SQLAlchemy URL (SQLite dev, Postgres prod) |
| `SECRET_KEY` | dev-only in dev, generated in Docker | JWT signing key — generated automatically by the container, or supply your own and keep it secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Session lifetime (8 h) |
| `CORS_ORIGINS` | `["*"]` | Allowed origins (JSON list string) |
| `DAYS_WATER_PER_PERSON` | `3.0` | Simulator water rate (gallons) |
| `RICE_SACKS_PER_PERSON` | `0.1` | Simulator rice rate (50 kg sacks) |
| `AVG_PERSONS_PER_HOUSEHOLD` | `4` | Simulator household-to-evacuee multiplier |
| `SEED_DEMO_DATA` | `true` in Compose | Fill an empty database with demo accounts on API start |

### Startup guards

The app refuses to boot on an unsafe production configuration rather than
starting with a known-bad secret:

- **`SECRET_KEY` is a known placeholder while `DATABASE_URL` is not SQLite** →
  raises at startup. This covers the development default, the default that used to
  ship in `docker-compose.yml`, and anything still containing `change-me`,
  `dev-only`, `placeholder`, `example` or `your-secret`, or shorter than 32
  characters. A placeholder would let anyone mint valid admin tokens. Generate one
  with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The container
  entrypoint intercepts the common cases and generates a key instead, so this guard
  is a backstop rather than something you will hit in normal use.
- **`CORS_ORIGINS` mixes `*` with explicit origins** → raises at startup. Pick
  one: either the wildcard (no credentials) or an explicit list (credentials
  allowed). When the wildcard is used, `allow_credentials` is disabled
  automatically, since browsers reject credentialed wildcard requests anyway.

> Note for tooling: `alembic/env.py` imports `app.core.config`, so migrations need a
> valid `SECRET_KEY` too when pointing at Postgres. Inside the container the
> entrypoint has already generated one, so this only affects manual runs.

---

## Ops notes

- **Backups:** SQLite = copy `backend/disaster_prep.db`; Postgres = `pg_dump`.
- **Logs:** uvicorn logs to stdout (`docker compose logs -f api`).
- **Health check:** `GET /health` → `{"status": "ok"}`.
- **Monitoring hooks:** the only stateful writes beyond CRUD are `stock_transactions` (audit) and `evacuation_assignments` (allocation history) — both are append-only ledger tables.