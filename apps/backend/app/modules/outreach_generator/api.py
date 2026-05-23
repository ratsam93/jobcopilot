from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.backend.app.auth import UserPublic, current_user
from apps.backend.app.persistence_repos import OutreachDraftRepository
from apps.backend.app.shared.contracts import OutreachEmailResult

router = APIRouter()
repo = OutreachDraftRepository()


class GmailDraftRequest(BaseModel):
    outreach_draft_id: str


@router.post("/outreach-drafts/gmail-draft")
async def create_gmail_draft(payload: GmailDraftRequest, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    draft_payload = repo.get(payload.outreach_draft_id)
    if draft_payload is None:
        raise HTTPException(status_code=404, detail="Outreach draft not found")
    gmail_payload = draft_payload.get("gmail_draft")
    if not gmail_payload:
        raise HTTPException(status_code=422, detail="Draft is not ready for Gmail")
    gmail_draft_id = f"gmail-draft-{payload.outreach_draft_id}"
    repo.mark_gmail_draft(payload.outreach_draft_id, gmail_draft_id, "drafted", gmail_payload)
    validated = OutreachEmailResult.model_validate(draft_payload)
    return {
        "outreach_draft_id": validated.outreach_draft_id,
        "gmail_draft_id": gmail_draft_id,
        "gmail_draft_status": "drafted",
        "status": validated.status,
    }
