from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from apps.backend.app.modules.campaign_planner.api import router as campaign_router
from apps.backend.app.modules.career_vault.api import router as career_vault_router


app = FastAPI(title="Job Copilot Backend", version="0.1.0")
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


if frontend_dist.exists():

    @app.get("/{path:path}")
    async def spa_fallback(path: str) -> FileResponse:
        candidate = frontend_dist / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
