from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from .models import CampaignCreateInput, CampaignParseInput
from .service import store

router = APIRouter()


@router.post("/campaigns/create")
async def create_campaign(payload: CampaignCreateInput) -> dict[str, object]:
    return store.create_campaign(payload).model_dump()


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID) -> dict[str, object]:
    return store.get_campaign(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/parse")
async def parse_campaign(campaign_id: UUID, payload: CampaignParseInput) -> dict[str, object]:
    return store.parse_campaign(campaign_id, payload).model_dump()


@router.post("/campaigns/{campaign_id}/run")
async def run_campaign(campaign_id: UUID) -> dict[str, object]:
    return store.start_run(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID) -> dict[str, object]:
    return store.pause(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: UUID) -> dict[str, object]:
    return store.cancel(campaign_id).model_dump()


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: UUID) -> dict[str, object]:
    return store.status(campaign_id)


@router.get("/campaigns/{campaign_id}/jobs")
async def campaign_jobs(campaign_id: UUID) -> list[dict[str, object]]:
    return store.list_jobs(campaign_id)
