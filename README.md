# Job Copilot Platform

Backend-first modular monolith for AI-assisted job search and campaign execution, with a separate React/Vite frontend.

## Status

- Spec scaffold created.
- Implementation has not started yet.
- SRS 2.0 repository strategy is now documented under `docs/srs/`.
- Frontend lives in `frontend/`.
- Backend lives in `apps/backend/`.

## Specs

- `specs/job-copilot-backend/plan.md`
- `specs/job-copilot-backend/tasks.md`
- `docs/srs/SRS-2.0-Repo-Clone-and-Modular-Build-Update.md`

## Frontend

- `frontend/`
- `cd frontend && npm install`
- `cd frontend && npm run dev`

## Backend

- `apps/backend/`
- `python -m uvicorn apps.backend.app.main:app --reload`

## Docker Deployment

This repository is configured for Docker Compose deployment to a Contabo VPS.

### Runtime layout

- The root `Dockerfile` builds the Vite frontend and packages it into the FastAPI image.
- The backend serves the SPA from `/` and the API from `/api/*`.
- `docker-compose.yml` runs a single production container named `jobcopilot`.

### Required GitHub Secrets

- `HOST`
- `USERNAME`
- `PORT`
- `SSH_KEY`

### Deployment flow

1. Push to `main`.
2. GitHub Actions syncs the repository to `/opt/projects/jobcopilot` over SSH.
3. The workflow runs `docker compose up -d --build --remove-orphans` on the VPS.

### Server prerequisites

- Docker and Docker Compose v2 installed on the VPS.
- SSH access for the GitHub Actions deploy user.
- The target folder `/opt/projects/jobcopilot` must exist and be writable.

### Local production test

- `docker compose up --build`
- Open `http://localhost:8000`
