FROM node:20-alpine AS frontend-builder
WORKDIR /src/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

COPY pyproject.toml ./
COPY apps ./apps
COPY --from=frontend-builder /src/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["sh", "-c", "uvicorn apps.backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
