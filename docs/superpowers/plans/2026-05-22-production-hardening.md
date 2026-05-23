# Job Copilot Production Hardening Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current deployable prototype into a production-shaped stack with separate frontend, API, worker, and infrastructure services.

**Architecture:** Keep the existing FastAPI and React codebase, but move runtime concerns into Docker Compose-managed services. The backend will run as an API container plus a worker container, both using the same Python image, while PostgreSQL and Redis provide durable storage and queue primitives. The frontend will build into a separate Nginx container that proxies `/api` to the backend service.

**Tech Stack:** FastAPI, React, Vite, Docker Compose, PostgreSQL, Redis, Nginx, GitHub Actions, pytest

---

### Task 1: Split runtime images by responsibility

**Files:**
- Create: `apps/backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `Dockerfile`
- Modify: `frontend/nginx.conf`

- [ ] **Step 1: Write the failing deployment shape test**

```bash
docker compose config
```

Expected before the change: the stack does not express separate backend and worker runtime images.

- [ ] **Step 2: Build the backend image**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY apps ./apps
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir fastapi uvicorn pydantic
RUN pip install --no-cache-dir -e .
CMD ["uvicorn", "apps.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Build the frontend image**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/frontend/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 4: Update compose to add backend, worker, Postgres, and Redis**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: jobcopilot
      POSTGRES_USER: jobcopilot
      POSTGRES_PASSWORD: jobcopilot
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: apps/backend/Dockerfile
    environment:
      JOBCOPILOT_DATABASE_URL: postgresql+psycopg://jobcopilot:jobcopilot@postgres:5432/jobcopilot
      JOBCOPILOT_REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  worker:
    build:
      context: .
      dockerfile: apps/backend/Dockerfile
    command: python -m apps.backend.app.worker
    environment:
      JOBCOPILOT_DATABASE_URL: postgresql+psycopg://jobcopilot:jobcopilot@postgres:5432/jobcopilot
      JOBCOPILOT_REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

- [ ] **Step 5: Run the compose config check again**

```bash
docker compose config
```

Expected: a single coherent runtime topology with five services.

### Task 2: Add backend worker and deployment configuration

**Files:**
- Create: `apps/backend/app/worker.py`
- Modify: `apps/backend/app/config.py`
- Modify: `apps/backend/app/main.py`

- [ ] **Step 1: Write a worker entrypoint**

```python
from apps.backend.app.config import settings

def main() -> None:
    print(f"Job Copilot worker starting with database={settings.database_url}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make settings explicit for runtime URLs**

```python
from pydantic import BaseModel

class Settings(BaseModel):
    database_url: str = "sqlite:///./jobcopilot.db"
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
```

- [ ] **Step 3: Keep the API health endpoint stable**

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

### Task 3: Align frontend deployment and proxy behavior

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Confirm `/api` is the only backend surface**
- [ ] **Step 2: Keep the UI functional when backend is unavailable**
- [ ] **Step 3: Preserve production build output**

### Task 4: Verify the deployable stack

**Files:**
- Modify: none

- [ ] **Step 1: Run backend tests**

```bash
pytest tests -q
```

- [ ] **Step 2: Build the frontend**

```bash
cd frontend
npm run build
```

- [ ] **Step 3: Verify compose topology**

```bash
docker compose config
```

- [ ] **Step 4: Smoke test the deployment URLs**

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000
```

