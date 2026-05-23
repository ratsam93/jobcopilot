from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from apps.backend.app.auth import UserPublic, current_user

from .models import BulletInput, ClaimInput, DoNotClaimInput, ProfileUpdateInput, SkillInput
from .service import store

router = APIRouter()


@router.post("/career-vault/resume/upload")
async def upload_resume(
    resume: bytes = Body(..., media_type="application/octet-stream"),
    x_filename: str | None = Header(default=None, alias="X-Filename"),
    user: UserPublic = Depends(current_user),
) -> dict[str, object]:
    if not x_filename:
        raise HTTPException(status_code=400, detail="X-Filename header is required")
    result = store.create_or_update_profile_from_bytes(resume, filename=x_filename)
    return result.model_dump()


@router.get("/career-vault/profile/{candidate_profile_id}")
async def get_profile(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.profile_summary(candidate_profile_id)


@router.post("/career-vault/profile/{candidate_profile_id}/update")
async def update_profile(candidate_profile_id: UUID, payload: ProfileUpdateInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.update_profile(candidate_profile_id, payload).model_dump()


@router.get("/career-vault/profile/{candidate_profile_id}/skills")
async def list_skills(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    return [skill.model_dump() for skill in store.get_profile(candidate_profile_id).skills]


@router.post("/career-vault/profile/{candidate_profile_id}/skills")
async def create_skill(candidate_profile_id: UUID, payload: SkillInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.add_skill(candidate_profile_id, payload).model_dump()


@router.post("/career-vault/profile/{candidate_profile_id}/approved-claims")
async def create_claim(candidate_profile_id: UUID, payload: ClaimInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.add_claim(candidate_profile_id, payload).model_dump()


@router.post("/career-vault/profile/{candidate_profile_id}/do-not-claim")
async def create_do_not_claim(candidate_profile_id: UUID, payload: DoNotClaimInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.add_do_not_claim(candidate_profile_id, payload).model_dump()


@router.get("/career-vault/profile/{candidate_profile_id}/bullet-bank")
async def list_bullets(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> list[dict[str, object]]:
    return [bullet.model_dump() for bullet in store.get_profile(candidate_profile_id).bullet_bank]


@router.post("/career-vault/profile/{candidate_profile_id}/bullet-bank")
async def create_bullet(candidate_profile_id: UUID, payload: BulletInput, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.add_bullet(candidate_profile_id, payload).model_dump()
