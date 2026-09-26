# Local Disaster Preparedness System

This project is a full-stack disaster preparedness dashboard for local officials and responders. It includes household records, evacuation centers, resource tracking, incident reporting, allocation planning, and scenario simulation.

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

The app is designed to be demo-ready for local operations planning and internal reviews.

## Environment variables

Create a `.env` file in the backend root if needed:

```env
DATABASE_URL=sqlite:///./disaster_prep.db
API_PREFIX=/api
```

## Docker

```bash
docker compose up --build
```

This runs the backend, frontend, and Postgres service together.
