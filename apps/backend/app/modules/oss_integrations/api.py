from __future__ import annotations

from fastapi import APIRouter

from apps.backend.app.modules.oss_integrations.service import OSSIntegrationRegistry, list_oss_integrations


router = APIRouter(prefix="/oss", tags=["oss-integrations"])


@router.get("/integrations")
async def get_oss_integrations() -> OSSIntegrationRegistry:
    return list_oss_integrations()
