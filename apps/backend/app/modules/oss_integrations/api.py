from __future__ import annotations

from fastapi import APIRouter

from apps.backend.app.modules.oss_integrations.langgraph_probe import LangGraphProbeResult, run_langgraph_probe
from apps.backend.app.modules.oss_integrations.pydantic_ai_probe import (
    PydanticAIProbeResult,
    run_pydantic_ai_probe,
)
from apps.backend.app.modules.oss_integrations.service import OSSIntegrationRegistry, list_oss_integrations


router = APIRouter(prefix="/oss", tags=["oss-integrations"])


@router.get("/integrations")
async def get_oss_integrations() -> OSSIntegrationRegistry:
    return list_oss_integrations()


@router.post("/langgraph/probe", response_model=LangGraphProbeResult)
async def post_langgraph_probe() -> LangGraphProbeResult:
    return run_langgraph_probe()


@router.post("/pydantic-ai/probe", response_model=PydanticAIProbeResult)
async def post_pydantic_ai_probe() -> PydanticAIProbeResult:
    return run_pydantic_ai_probe()
