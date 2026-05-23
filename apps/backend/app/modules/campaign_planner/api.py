from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from apps.backend.app.auth import UserPublic, current_user

from .models import CampaignCreateInput, CampaignParseInput
from .service import store
from apps.backend.app.worker_tasks import run_campaign as enqueue_run_campaign
from apps.backend.app.workflow_runs import workflow_runs

router = APIRouter()


@router.post("/campaigns/create")
async def create_campaign(payload: CampaignCreateInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    payload.user_id = user.id
    return store.create_campaign(payload).model_dump()


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.get_campaign(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/parse")
async def parse_campaign(campaign_id: UUID, payload: CampaignParseInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.parse_campaign(campaign_id, payload).model_dump()


@router.post("/campaigns/{campaign_id}/run")
async def run_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    run = workflow_runs.create("run_campaign", {"campaign_id": str(campaign_id)})
    enqueue_run_campaign.delay(str(campaign_id), run["id"])
    return {"workflow_run_id": run["id"], "status": "queued", "campaign_id": str(campaign_id)}


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.pause(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.cancel(campaign_id).model_dump()


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.status(campaign_id)


@router.get("/campaigns/{campaign_id}/jobs")
async def campaign_jobs(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    return store.list_jobs(campaign_id)
