from __future__ import annotations

import re
from uuid import UUID, uuid4

from fastapi import HTTPException

from apps.backend.app.repositories import CampaignRepository

from .models import (
    Campaign,
    CampaignConstraint,
    CampaignCreateInput,
    CampaignRun,
    CampaignStatus,
    CampaignParseInput,
    JobSummary,
    StructuredQuery,
)
from ..career_vault.service import store as career_store
from ..career_vault.service import utc_now


class CampaignPlannerStore:
    def __init__(self) -> None:
        self.repo = CampaignRepository()

    def _persist(self, campaign: Campaign) -> Campaign:
        self.repo.upsert(campaign)
        return campaign

    def _build_campaign_name(self, prompt: str) -> str:
        prompt = prompt.strip().rstrip(".")
        words = re.sub(r"[^A-Za-z0-9 ]+", " ", prompt).split()
        return " ".join(words[:6]) or "Campaign"

    def _infer_query(self, prompt: str, candidate_profile_id: UUID | None = None) -> StructuredQuery:
        lowered = prompt.lower()
        countries = ["United States"] if any(token in lowered for token in ("us", "usa", "united states", "america")) else []
        locations = ["Remote", "Global Remote", "US Remote"] if "remote" in lowered or countries else []
        company_types = []
        for company_type in ("technology", "saas", "ai", "cloud", "product", "finance", "healthcare"):
            if company_type in lowered:
                company_types.append(company_type.title())
        if not company_types:
            company_types = ["Technology", "SaaS", "AI", "Cloud", "Product"]
        role_tracks: list[str] = ["auto_detect"]
        if candidate_profile_id:
            profile = career_store.get_profile(candidate_profile_id)
            if profile.target_roles:
                role_tracks = [role.replace(" ", "_") for role in profile.target_roles]
            elif profile.role_track:
                role_tracks = [profile.role_track]
        salary = {"minimum_usd": 30000, "ideal_usd": 100000} if countries or "tech" in lowered else {}
        minimum_fit_score = 75 if "top" in lowered or "best" in lowered else 70
        return StructuredQuery(
            target_countries=countries,
            target_locations=locations,
            company_types=company_types,
            role_tracks=role_tracks,
            minimum_fit_score=minimum_fit_score,
            salary=salary,
        )

    def _validate_query(self, query: StructuredQuery) -> StructuredQuery:
        if not query.target_countries and not query.target_locations:
            raise HTTPException(status_code=422, detail="Campaign must target at least one country or location")
        if query.minimum_fit_score < 50:
            raise HTTPException(status_code=422, detail="minimum_fit_score is too low")
        if query.include_cover_letter is False and query.include_resume_tailoring is False:
            raise HTTPException(status_code=422, detail="Campaign must enable at least one application asset")
        return query

    def create_campaign(self, payload: CampaignCreateInput) -> Campaign:
        if not payload.natural_language_prompt or not payload.natural_language_prompt.strip():
            raise HTTPException(status_code=422, detail="natural_language_prompt is required")
        if payload.candidate_profile_id:
            career_store.get_profile(payload.candidate_profile_id)
        structured_query = self._validate_query(self._infer_query(payload.natural_language_prompt, payload.candidate_profile_id))
        campaign = Campaign(
            campaign_id=uuid4(),
            user_id=payload.user_id,
            candidate_profile_id=payload.candidate_profile_id,
            natural_language_prompt=payload.natural_language_prompt,
            campaign_name=payload.campaign_name or self._build_campaign_name(payload.natural_language_prompt),
            structured_query=structured_query,
            execution_mode=payload.execution_mode or "approval_required",
        )
        campaign = self._persist(campaign)
        return campaign

    def parse_campaign(self, campaign_id: UUID, payload: CampaignParseInput) -> Campaign:
        campaign = self.get_campaign(campaign_id)
        prompt = payload.natural_language_prompt or campaign.natural_language_prompt
        campaign.structured_query = self._validate_query(self._infer_query(prompt, campaign.candidate_profile_id))
        campaign.campaign_name = self._build_campaign_name(prompt)
        campaign.status = "parsed"
        campaign.updated_at = utc_now()
        return self._persist(campaign)

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = self.repo.get(campaign_id)
        if campaign is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign

    def start_run(self, campaign_id: UUID) -> CampaignRun:
        campaign = self.get_campaign(campaign_id)
        run = CampaignRun(campaign_id=campaign_id, status="running", started_at=utc_now())
        campaign.runs.append(run)
        campaign.status = "running"
        campaign.updated_at = utc_now()
        campaign.jobs = [
            JobSummary(job_id=uuid4(), campaign_id=campaign_id, title="Queued job 1", company_name="Example AI", status="queued"),
            JobSummary(job_id=uuid4(), campaign_id=campaign_id, title="Queued job 2", company_name="Northstar Labs", status="queued"),
        ]
        self._persist(campaign)
        return run

    def pause(self, campaign_id: UUID) -> Campaign:
        campaign = self.get_campaign(campaign_id)
        campaign.status = "paused"
        campaign.updated_at = utc_now()
        return self._persist(campaign)

    def cancel(self, campaign_id: UUID) -> Campaign:
        campaign = self.get_campaign(campaign_id)
        campaign.status = "cancelled"
        campaign.updated_at = utc_now()
        return self._persist(campaign)

    def status(self, campaign_id: UUID) -> dict[str, object]:
        campaign = self.get_campaign(campaign_id)
        runs = getattr(campaign, "runs", [])
        jobs = getattr(campaign, "jobs", [])
        return {
            "campaign_id": campaign.campaign_id,
            "status": campaign.status,
            "execution_mode": campaign.execution_mode,
            "latest_run": runs[-1].model_dump() if runs else None,
            "job_count": len(jobs),
            "campaign_name": campaign.campaign_name,
            "structured_query": campaign.structured_query.model_dump(),
        }

    def list_jobs(self, campaign_id: UUID) -> list[dict[str, object]]:
        campaign = self.get_campaign(campaign_id)
        return [job.model_dump() for job in getattr(campaign, "jobs", [])]

    def add_constraint(self, campaign_id: UUID, constraint_type: str, constraint_value: str, mandatory: bool = True) -> CampaignConstraint:
        campaign = self.get_campaign(campaign_id)
        constraint = CampaignConstraint(
            campaign_id=campaign_id,
            constraint_type=constraint_type,
            constraint_value=constraint_value,
            mandatory=mandatory,
        )
        campaign.constraints.append(constraint)
        self._persist(campaign)
        return constraint


store = CampaignPlannerStore()
