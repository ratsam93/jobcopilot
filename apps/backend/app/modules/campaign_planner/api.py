from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from apps.backend.app.auth import UserPublic, current_user
from apps.backend.app.modules.review_queue.service import ReviewQueueService

from .models import CampaignCreateInput, CampaignParseInput, ManualJobInput
from .service import store
from apps.backend.app.worker_tasks import run_campaign as enqueue_run_campaign
from apps.backend.app.workflow_runs import workflow_runs

router = APIRouter()
review_service = ReviewQueueService()


@router.post("/campaigns/create")
async def create_campaign(payload: CampaignCreateInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    payload.user_id = user.id
    campaign = store.create_campaign(payload)
    return {
        "campaign_id": str(campaign.campaign_id),
        "status": "created",
        "approval_mode": campaign.execution_mode,
        "execution_mode": campaign.execution_mode,
        "structured_query": campaign.structured_query.model_dump(mode="json"),
        "parsed_campaign": campaign.model_dump(mode="json"),
    }


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
    return {
        "run_id": run["id"],
        "workflow_run_id": run["id"],
        "status": "queued",
        "current_step": "job_discovery",
        "campaign_id": str(campaign_id),
    }


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.pause(campaign_id).model_dump()


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.cancel(campaign_id).model_dump()


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.workflow_state(campaign_id)


@router.get("/campaigns/{campaign_id}/jobs")
async def campaign_jobs(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    return store.list_jobs(campaign_id)


@router.get("/campaigns/{campaign_id}/artifacts")
async def campaign_artifacts(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    state = store.workflow_state(campaign_id)
    return state["artifacts"]


@router.get("/campaigns/{campaign_id}/review-queue")
async def campaign_review_queue(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    state = store.workflow_state(campaign_id)
    return state["review_items"]


@router.post("/campaigns/{campaign_id}/review-queue/{review_id}/approve")
async def approve_review(campaign_id: UUID, review_id: str, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    item = review_service.set_status(review_id, "approved")
    return item.__dict__


@router.post("/campaigns/{campaign_id}/review-queue/{review_id}/reject")
async def reject_review(campaign_id: UUID, review_id: str, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    item = review_service.set_status(review_id, "rejected")
    return item.__dict__


@router.get("/campaigns/{campaign_id}/activity")
async def campaign_activity(campaign_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    state = store.workflow_state(campaign_id)
    return state["activity"]


@router.post("/campaigns/{campaign_id}/manual-job")
async def add_manual_job(campaign_id: UUID, payload: ManualJobInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.manual_job(campaign_id, payload.model_dump())
