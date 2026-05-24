from __future__ import annotations

import re
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import HTTPException

from apps.backend.app.persistence_repos import (
    ApplicationPackageRepository,
    AuditLogRepository,
    ReviewItemRepository,
    WorkflowRunRepository,
)
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
from ..document_generator.service import DocumentGeneratorService
from ..email_discovery.service import EmailDiscoveryService
from ..fit_scoring.service import FitScoringService
from ..job_discovery.service import Job, JobDiscoveryService
from ..outreach_generator.service import OutreachGeneratorService
from ..people_finder.service import PersonCandidate, PeopleFinderService
from ..review_queue.service import ReviewQueueService
from ..career_vault.service import store as career_store
from ..career_vault.service import utc_now


class CampaignPlannerStore:
    def __init__(self) -> None:
        self.repo = CampaignRepository()
        self.workflow_repo = WorkflowRunRepository()
        self.package_repo = ApplicationPackageRepository()
        self.review_repo = ReviewItemRepository()
        self.audit_repo = AuditLogRepository()

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
        discovered = JobDiscoveryService.with_default_oss_adapters().discover_and_persist()
        campaign.jobs = [
            JobSummary(
                job_id=uuid5(NAMESPACE_URL, record.normalized_job.job_id),
                campaign_id=campaign_id,
                title=record.normalized_job.title,
                company_name=record.normalized_job.company,
                source=record.normalized_job.source,
                source_url=record.normalized_job.source_url,
                location=record.normalized_job.location,
                remote=record.normalized_job.remote,
                status="discovered",
                reason="Imported from jobber OSS ATS adapter.",
            )
            for record in discovered
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

    def manual_job(self, campaign_id: UUID, payload: dict[str, object]) -> dict[str, object]:
        campaign = self.get_campaign(campaign_id)
        job = JobDiscoveryService.normalize(
            Job(
                source=str(payload.get("source", "manual")),
                source_url=str(payload.get("source_url", f"https://manual.local/{uuid4()}")),
                title=str(payload["role_title"]),
                company=str(payload["company_name"]),
                location=str(payload.get("location")) if payload.get("location") else None,
                remote=bool(payload.get("remote", False)),
                description=str(payload.get("description", "")),
                required_skills=list(payload.get("required_skills", [])),
            )
        )
        campaign.jobs.append(
            JobSummary(job_id=uuid4(), campaign_id=campaign_id, title=job.title, company_name=job.company, status="queued")
        )
        self._persist(campaign)
        return {
            "campaign_id": str(campaign_id),
            "job": job.model_dump(),
            "status": "queued",
            "reason": "Manual job added because no external job source is configured",
        }

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

    def workflow_state(self, campaign_id: UUID) -> dict[str, object]:
        campaign = self.get_campaign(campaign_id)
        latest_run = campaign.runs[-1] if campaign.runs else None
        run_payload = None
        steps: list[dict[str, object]] = []
        if latest_run:
            run_payload = self.workflow_repo.get(str(latest_run.id))
            details = (run_payload or {}).get("details_json") or {}
            steps = self._build_steps(campaign, run_payload, details)
        jobs = [job.model_dump() for job in getattr(campaign, "jobs", [])]
        packages = [row for row in self.package_repo.list_all() if row.get("job_id") in {job["job_id"] for job in jobs}]
        review_items = [row for row in self.review_repo.list_all() if row.get("review_id")]
        activity = [entry for entry in self.audit_repo.list() if str(entry.get("payload_json", {}).get("campaign_id", "")) in {str(campaign_id), ""}]
        return {
            "campaign_id": str(campaign.campaign_id),
            "run_id": run_payload["id"] if run_payload else None,
            "status": campaign.status,
            "current_step": self._current_step(run_payload),
            "steps": steps,
            "jobs": jobs,
            "jobs_discovered": len(jobs),
            "zero_jobs_reason": None if jobs else "No jobs discovered from configured jobber OSS ATS sources",
            "next_action": None if jobs else "Set JOBCOPILOT_JOBBER_SOURCES or add a manual job description",
            "artifacts": packages,
            "review_items": review_items,
            "activity": activity[-20:],
        }

    def _current_step(self, run_payload: dict[str, object] | None) -> str:
        if not run_payload:
            return "not_started"
        details = run_payload.get("details_json") or {}
        return str(details.get("task") or details.get("current_step") or run_payload.get("status") or "not_started")

    def _build_steps(self, campaign: Campaign, run_payload: dict[str, object] | None, details: dict[str, object]) -> list[dict[str, object]]:
        step_names = [
            "resume_parse",
            "campaign_create",
            "job_discovery",
            "fit_scoring",
            "document_generation",
            "outreach_drafting",
            "review_queue",
            "gmail_draft",
        ]
        run_status = (run_payload or {}).get("status", "queued")
        current_step = self._current_step(run_payload)
        output_map = {
            "job_discovery": details.get("discover_jobs"),
            "fit_scoring": details.get("score_jobs"),
            "document_generation": details.get("generate_documents"),
            "outreach_drafting": details.get("generate_outreach"),
            "review_queue": details.get("generate_outreach"),
        }
        steps: list[dict[str, object]] = []
        for name in step_names:
            status = "not_started"
            if name == "resume_parse" and campaign.candidate_profile_id:
                status = "complete"
            elif name == "campaign_create":
                status = "complete" if campaign.status in {"parsed", "running", "completed", "paused", "cancelled"} else "not_started"
            elif name == current_step:
                status = "running" if run_status == "running" else "complete"
            elif output_map.get(name):
                status = "complete"
            elif run_status == "failed":
                status = "failed" if name == current_step else "skipped"
            elif campaign.status == "running":
                status = "skipped" if name not in {current_step, "resume_parse", "campaign_create"} else "complete"
            steps.append(
                {
                    "name": name,
                    "status": status,
                    "input": details.get(name, {}),
                    "output": output_map.get(name),
                    "error": details.get("error") if name == current_step and run_status == "failed" else None,
                    "started_at": run_payload["details_json"].get("started_at") if run_payload else None,
                    "completed_at": run_payload["details_json"].get("completed_at") if run_payload else None,
                }
            )
        return steps


store = CampaignPlannerStore()
