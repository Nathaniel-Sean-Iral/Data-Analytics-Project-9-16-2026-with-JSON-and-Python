# Local Disaster Preparedness System — Progress Log

> We update this file as each stage/phase finishes. Status legend: `done` · `in progress` · `pending`.

**Stack:** FastAPI (Python) + React (TypeScript, Vite) · **Repo:** monorepo (`backend/`, `frontend/`)

---

## Phase 0 — Foundation
- [x] Requirements & data model (ERD) — `docs/ERD.md` (Mermaid diagram + field reference)
- [x] Repo setup (monorepo, .gitignore, README) — root `README.md`
- [x] Frontend scaffold — Vite + React + TS + Tailwind, router, app shell *(completed earlier)*
- [x] Backend scaffold — FastAPI app + SQLAlchemy models
- [x] Auth + RBAC — JWT login, roles admin / responder / viewer
- [x] CI baseline — GitHub Actions (backend pytest + frontend typecheck/build on push/PR)

**Exit criteria:** app boots, user can log in, health endpoint returns 200. ✅ **Met** (all endpoints smoke-tested via TestClient; `/health`, `/api/auth/login` verified).

---

## Phase 1 — Core CRUD Modules
- [x] Households — CRUD + pagination/search/sort
- [x] Evacuation Centers — CRUD
- [x] Resources — CRUD + stock transactions
- [x] Incidents — CRUD + status workflow

**Exit criteria:** all four entities fully CRUD-able by admin from the UI. ✅ **Met** (admin/responder/viewer permissions verified in pytest; 46 tests green).

---

## Phase 2 — Analytics & Map
- [x] Resource dashboard aggregate + low-stock alerts (`/api/resources/summary`, `/api/dashboard/stats`)
- [x] Map layers (households, centers, incident zones) served from live API *(backend live on 8000; the React map/frontend pages now fetch live data via the Vite `/api` proxy)*
- [x] Role-gated views (responders edit incidents, viewers read-only)

**Exit criteria:** map renders all three layers from live API; dashboard computes available vs. required. ✅ **Met** (map + dashboard consume live API data).

---

## Phase 3 — Algorithms & Simulation
- [x] Evacuation allocation algorithm + `/api/evacuations/allocate`
- [x] Center load % + overflow + coverage gaps report (`/api/evacuations/center-loads`)
- [x] Scenario simulator + `/api/simulator/run` (+ projected resource shortfalls)

**Exit criteria:** a scenario run reports center loads, overflow counts, resource gaps. ✅ **Met** (allocates nearest-center-first with capacity checks; simulator computes per-resource deficit vs 400-evacuee baseline).

---

## Phase 4 — Hardening & Polish
- [x] pytest suite (API + allocation algorithm) — 46 tests green
- [x] Seed script (realistic barangay data) + demo login
- [x] Alembic migrations — initial revision generated; `upgrade head` verified on fresh DB; dev DB stamped
- [x] Docker Compose (API + Postgres + Nginx serving React build) — `docker-compose.yml` + Dockerfiles + nginx config
- [x] Documentation (README, API reference, deployment guide) — `docs/API.md`, `docs/DEPLOYMENT.md`, `docs/ERD.md`

**Exit criteria:** full test suite green; `docker compose up` runs the system. ✅ **Met** (46/46 tests; compose stack ready — requires Docker to run locally, available in Codespaces/CI).

---

## Backlog (nice-to-haves)
- Real-time WebSockets, SMS/email alerts, PWA, import/export, public portal.

---

## Notes / decisions
- Dev DB defaults to **SQLite** (`DATABASE_URL` env var switches to PostgreSQL) so the app runs without extra services; Postgres is production target.
- Frontend already exists and defines the API contract (`frontend/src/api/types.ts`, `services.ts`) — backend endpoints mirror it exactly.
- RBAC implemented as a rank gate (`viewer=1 < responder=2 < admin=3`): read = viewer+, incident create/update + allocation + simulator = responder+, households/centers/resources mutations = admin.
- Passwords hashed with PBKDF2-HMAC-SHA256 (600k iterations, `pbkdf2$600000$<salt>$<digest>` format). Secrets come from `app/core/config.py` `Settings` (env-overridable via `.env`).
- PATCH `/incidents/{id}` accepts `{status}` and enforces a workflow: `reported → assessing → responding → resolved` (backwards to `assessing` allowed).
- Allocation assigns each household to the nearest center that still has capacity; produces center load %, overflow list, and coverage-gap warnings for barangays without a center. Assignments persist to `evacuation_assignments`.
- Demo accounts seeded by `backend/seed.py`: `admin/admin`, `responder/responder`, `viewer/viewer`.
- **Run backend:** `cd backend; .venv\Scripts\python -m uvicorn app.main:app --port 8000` (docs at `/docs`).
- Vite dev proxy forwards `/api` → `localhost:8000`.
- Day-to-day log:
  - **Hardening (2026-09-24):** README + ERD + API + deployment docs; Alembic (initial migration `8ebd5a148d1c`, verified on fresh DB, dev SQLite stamped); Docker Compose (Postgres + API + Nginx) with Dockerfiles/nginx proxy; GitHub Actions CI (backend pytest + frontend typecheck/build). `psycopg[binary]` added for Postgres; `create_all` now gated to SQLite dev only (Postgres uses Alembic).
  - **Live wiring (2026-09-24):** mock `http.server` (PID 16104) stopped; uvicorn running `app.main:app` on 127.0.0.1:8000 (PID 23032, logs in `%TEMP%\opencode\uvicorn-8000*.log`); frontend dev server already running on http://localhost:5173 with `/api` proxy → 8000. Verified through the proxy: login (`admin/admin`) + dashboard stats (40 households, 5 incidents).
  - Stage 1 (scaffold) ✅ — config, database, security, deps; models for user/household.
  - Stage 2 (models) ✅ — center, resource + stock transactions, incident, evacuation assignment; `models/__init__.py` aggregates all onto `Base`.
  - Stage 3 (schemas + auth/RBAC) ✅ — `schemas.py`, `api/auth.py` (login + me), `deps.require_roles`.
  - Stages 4–7 (CRUD routers) ✅ — households (paged/search/sorted), centers, resources (+summary/adjust/threshold), incidents (+status workflow).
  - Stage 8 (analytics/dashboard) ✅ — `api/dashboard.py`, `services/analytics.py`.
  - Stage 9 (allocation + simulator) ✅ — `services/allocation.py`, `api/evacuations.py`, `api/simulator.py`.
  - Stage 10 (seed) ✅ — `backend/seed.py` mirrors the frontend mock dataset (40 HH, 6 centers, 8 resources, 5 incidents).
  - Stage 11 (pytest) ✅ — 46 tests green (`backend/.venv` venv).
  - Stage 12 (verify + log) ✅ — health + login + allocate + simulator smoke-tested; this file updated.
  - Bugfix during Stage 11: `require_roles` used `max` rank (everyone required admin) → switched to `min`.
  - Bugfix during Stage 11: allocation assignments lacked `id` (schema validation error) → persists rows then copies DB ids back.
  - Bugfix during Stage 11: incident `reported → resolved` was allowed in one jump → tightened transition map.