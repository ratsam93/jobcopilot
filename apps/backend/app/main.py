from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from apps.backend.app.database import check_database
from apps.backend.app.config import settings
from apps.backend.app.db_init import initialize_database
from apps.backend.app.modules.campaign_planner.api import router as campaign_router
from apps.backend.app.modules.career_vault.api import router as career_vault_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Job Copilot Backend", version="0.1.0", lifespan=lifespan)
frontend_dist = Path("/app/frontend/dist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(career_vault_router, prefix="/api")
app.include_router(campaign_router, prefix="/api")

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/")
    async def spa_index() -> FileResponse:
        return FileResponse(frontend_dist / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/dependencies")
async def dependency_health() -> dict[str, str]:
    return {
        "app_env": settings.app_env,
        "database_url": settings.database_url,
        "redis_url": settings.redis_url,
        "qdrant_url": settings.qdrant_url or "unset",
    }


@app.get("/health/database")
async def database_health() -> dict[str, str]:
    return {
        "status": "ok" if check_database(settings.database_url) else "unavailable",
        "database_url": settings.database_url,
    }


if frontend_dist.exists():

    @app.get("/{path:path}")
    async def spa_fallback(path: str) -> FileResponse:
        candidate = frontend_dist / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
