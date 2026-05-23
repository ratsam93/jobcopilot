# Job Copilot Platform

Production-oriented job search and campaign workflow stack with a separate React/Vite frontend, a FastAPI backend, and Docker Compose deployment.

## Repository layout

- `apps/backend/` - FastAPI API, Celery task modules, database bootstrap, worker entrypoint
- `frontend/` - React + Vite UI
- `docker-compose.yml` - production/local compose stack
- `requirements.txt` - runtime Python dependencies for the backend
- `requirements-dev.txt` - runtime dependencies plus test tooling
- `.env.example` - environment template for the server
- `alembic/` and `alembic.ini` - database migrations
- `tests/` - integration, end-to-end, and unit coverage
- `docs/` - SRS and planning documents
- `research/oss-reference/` - cloned OSS reference repos only

## Production dependencies

Install the backend runtime requirements on the server:

```bash
python -m pip install -r requirements.txt
```

For local development and tests:

```bash
python -m pip install -r requirements-dev.txt
```

Alembic commands:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Run with Docker Compose

Start the full stack:

```bash
docker compose up -d --build
```

Services:

- frontend: `http://127.0.0.1:3000`
- backend health: `http://127.0.0.1:8000/health`
- database health: `http://127.0.0.1:8000/health/database`

Check status and logs:

```bash
docker compose ps
docker compose logs -f
```

The `worker` service runs the Celery worker process backed by Redis.

Stop the stack:

```bash
docker compose down
```

## Run locally without Docker

Backend:

```bash
python -m pip install -r requirements-dev.txt
python -m uvicorn apps.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Tests

Run the complete backend test pack:

```bash
pytest tests -q
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Deployment

GitHub Actions deploys to the VPS at `/opt/projects/jobcopilot` using the repository copy on `main`.

Required secrets:

- `HOST`
- `USERNAME`
- `PORT`
- `SSH_KEY`

## Notes

- PostgreSQL and Redis are included in Compose.
- The backend currently persists the initial schema and health checks; domain services are still being migrated from in-memory stores.
- OSS reference clones stay under `research/oss-reference/` and are not part of the production runtime.
- The old root-level single-container `Dockerfile` has been removed. Use `apps/backend/Dockerfile` and `frontend/Dockerfile` through Compose.
- Compose runs database migrations before backend startup through the backend container command.
