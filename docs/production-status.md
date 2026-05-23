# Job Copilot Production Status

Last updated: 2026-05-23

## What has been developed

- React + Vite frontend in `frontend/`
- FastAPI backend in `apps/backend/`
- Docker Compose deployment stack in `docker-compose.yml`
- GitHub Actions deploy workflow in `.github/workflows/deploy.yml`
- Production requirements files:
  - `requirements.txt`
  - `requirements-dev.txt`
- Backend persistence layer:
  - SQLAlchemy engine/session setup
  - Postgres-backed tables for career profiles, campaigns, audit logs, and workflow runs
- Backend workflow modules:
  - Career Vault
  - Campaign Planner
  - Job Discovery
  - Fit Scoring
  - Document Generation
  - People Finder
  - Email Discovery
  - Outreach Generation
  - Review Queue
  - Tracker
- Frontend workflow console:
  - resume upload
  - campaign creation
  - campaign run
  - workflow status
  - queued jobs
  - API connection summary
  - workflow explanation sections

## What is running on the server

Current deployment target:

- `/opt/projects/jobcopilot`

Running services:

- `postgres`
- `redis`
- `backend`
- `worker`
- `frontend`

Ports:

- Frontend: `http://158.220.113.185:3000`
- Backend: `http://158.220.113.185:8000`
- Backend health: `http://158.220.113.185:8000/health`
- Backend database health: `http://158.220.113.185:8000/health/database`

## What the UI shows now

- Workflow flow from intake to approval
- How a job is applied
- What artifacts are created
- API endpoints used by the application
- Resume upload and campaign controls
- Workflow status and queued jobs

## Deployment behavior

- Pushes to `main` trigger `.github/workflows/deploy.yml`
- GitHub Actions copies the repo to the VPS
- The workflow runs `docker compose up -d --build --remove-orphans`
- Compose uses Postgres health checks so backend startup waits for the database

## Remaining production work

- Move the remaining in-memory domain stores onto Postgres
- Add Alembic migrations
- Replace the worker placeholder with a real queue consumer
- Add authentication and per-user isolation
- Wire durable external integrations

## Important repo files

- `README.md`
- `docker-compose.yml`
- `.github/workflows/deploy.yml`
- `requirements.txt`
- `requirements-dev.txt`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `apps/backend/app/main.py`
- `apps/backend/app/db_init.py`
- `apps/backend/app/repositories.py`
