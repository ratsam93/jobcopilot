from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend.app.auth import UserPublic, current_user

from .models import BulletInput, ClaimInput, DoNotClaimInput, ProfileUpdateInput, SkillInput
from .service import store

router = APIRouter()


@router.post("/career-vault/resume/upload")
async def upload_resume(
    request: Request,
    user: UserPublic = Depends(current_user),
) -> dict[str, object]:
    content_type = request.headers.get("content-type", "")
    filename = request.headers.get("x-filename", "resume.txt")
    payload = b""
    resume_text = None
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        resume_file = form.get("resume_file")
        if resume_file is not None:
            filename = getattr(resume_file, "filename", None) or filename
            content_type = getattr(resume_file, "content_type", None) or content_type
            payload = await resume_file.read()
        else:
            resume_text = form.get("resume_text")
            if form.get("resume_filename"):
                filename = str(form.get("resume_filename"))
    else:
        payload = await request.body()
        if not payload:
            resume_text = request.query_params.get("resume_text")
    if resume_text is not None and not payload:
        payload = str(resume_text).encode("utf-8")
        content_type = "text/plain"
    if not payload:
        raise HTTPException(status_code=400, detail="Upload a file or provide resume_text")
    result = store.create_or_update_profile_from_bytes(payload, filename=filename)
    parsed_resume = store.parsed_profile(result.candidate_profile_id)
    return {
        "status": "success",
        "parse_status": result.parse_status,
        "upload_status": result.parse_status,
        "candidate_profile_id": str(result.candidate_profile_id),
        "profile_id": str(result.candidate_profile_id),
        "source_filename": result.source_filename,
        "filename": result.source_filename,
        "content_type": content_type,
        "file_size": len(payload),
        "text_length": len(result.extracted_text),
        "created_at": result.created_profile.created_at,
        "server_saved": True,
        "created_profile": result.created_profile.model_dump(mode="json"),
        "parsed_resume": parsed_resume,
        "warnings": parsed_resume.get("parser_warnings", []),
        "raw_response": result.model_dump(mode="json"),
    }


@router.get("/career-vault/profile/{candidate_profile_id}")
async def get_profile(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.profile_summary(candidate_profile_id)


@router.get("/career-vault/profiles/{candidate_profile_id}")
async def get_profile_alias(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.profile_summary(candidate_profile_id)


@router.get("/career-vault/profiles/{candidate_profile_id}/parsed")
async def get_profile_parsed(candidate_profile_id: UUID, user: UserPublic = Depends(current_user)) -> dict[str, object]:
    return store.parsed_profile(candidate_profile_id)


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
