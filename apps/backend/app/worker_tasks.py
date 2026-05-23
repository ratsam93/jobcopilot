from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from apps.backend.app.celery_app import celery_app
from apps.backend.app.core_kernel.workflow_state import WorkflowStatus
from apps.backend.app.modules.campaign_planner.service import store as campaign_store
from apps.backend.app.modules.career_vault.service import store as career_store
from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.email_discovery.service import EmailDiscoveryService
from apps.backend.app.modules.fit_scoring.service import FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PersonCandidate, PeopleFinderService
from apps.backend.app.modules.review_queue.service import ReviewQueueService
from apps.backend.app.workflow_runs import workflow_runs


def _workflow_context(campaign_id: str) -> dict[str, object]:
    campaign = campaign_store.get_campaign(UUID(campaign_id))
    profile = None
    if campaign.candidate_profile_id:
        profile = career_store.get_profile(campaign.candidate_profile_id)
    return {"campaign": campaign, "profile": profile}


@celery_app.task(name="run_campaign")
def run_campaign(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    workflow_run = workflow_run_id or workflow_runs.create("run_campaign", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(workflow_run, {"campaign_id": campaign_id, "task": "run_campaign", "current_step": "job_discovery"})
    try:
        discover_result = discover_jobs(campaign_id, workflow_run)
        score_result = score_jobs(campaign_id, workflow_run)
        document_result = generate_documents(campaign_id, workflow_run)
        people_result = find_people(campaign_id, workflow_run)
        outreach_result = generate_outreach(campaign_id, workflow_run)
        result = {
            "workflow_run_id": workflow_run,
            "campaign_id": campaign_id,
            "discover_jobs": discover_result,
            "score_jobs": score_result,
            "generate_documents": document_result,
            "find_people": people_result,
            "generate_outreach": outreach_result,
        }
        workflow_runs.mark_succeeded(workflow_run, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(workflow_run, str(exc), {"campaign_id": campaign_id, "task": "run_campaign"})
        raise


@celery_app.task(name="discover_jobs")
def discover_jobs(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    run_id = workflow_run_id or workflow_runs.create("discover_jobs", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(run_id, {"campaign_id": campaign_id, "task": "discover_jobs", "current_step": "job_discovery"})
    try:
        campaign = campaign_store.start_run(UUID(campaign_id))
        result = {"campaign_id": campaign_id, "job_count": len(campaign_store.list_jobs(UUID(campaign_id)))}
        workflow_runs.mark_succeeded(run_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(run_id, str(exc), {"campaign_id": campaign_id, "task": "discover_jobs"})
        raise


@celery_app.task(name="score_jobs")
def score_jobs(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    run_id = workflow_run_id or workflow_runs.create("score_jobs", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(run_id, {"campaign_id": campaign_id, "task": "score_jobs", "current_step": "fit_scoring"})
    try:
        context = _workflow_context(campaign_id)
        campaign = context["campaign"]
        profile = context["profile"]
        jobs = campaign_store.list_jobs(UUID(campaign_id))
        scored = []
        if profile and jobs:
            scorer = FitScoringService()
            for job in jobs:
                normalized_job = Job(
                    source="campaign",
                    source_url=f"https://example.com/{job['job_id']}",
                    title=job["title"],
                    company=job["company_name"],
                    remote=True,
                    required_skills=["FastAPI", "SQL"],
                )
                scored.append(scorer.score(JobDiscoveryService.normalize(normalized_job), profile))
        result = {"campaign_id": campaign_id, "scored_jobs": len(scored), "campaign_status": campaign.status}
        workflow_runs.mark_succeeded(run_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(run_id, str(exc), {"campaign_id": campaign_id, "task": "score_jobs"})
        raise


@celery_app.task(name="generate_documents")
def generate_documents(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    run_id = workflow_run_id or workflow_runs.create("generate_documents", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(run_id, {"campaign_id": campaign_id, "task": "generate_documents", "current_step": "document_generation"})
    try:
        context = _workflow_context(campaign_id)
        profile = context["profile"]
        campaign = context["campaign"]
        jobs = campaign_store.list_jobs(UUID(campaign_id))
        if profile is None or not jobs:
            result = {"campaign_id": campaign_id, "packages_created": 0}
        else:
            scorer = FitScoringService()
            package_service = DocumentGeneratorService()
            normalized = JobDiscoveryService.normalize(
                Job(
                    source="campaign",
                    source_url=f"https://example.com/{jobs[0]['job_id']}",
                    title=jobs[0]["title"],
                    company=jobs[0]["company_name"],
                    remote=True,
                    required_skills=["FastAPI", "SQL"],
                )
            )
            score = scorer.score(normalized, profile)
            package_service.generate_package(normalized, profile, score)
            result = {"campaign_id": campaign_id, "packages_created": 1, "campaign_status": campaign.status}
        workflow_runs.mark_succeeded(run_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(run_id, str(exc), {"campaign_id": campaign_id, "task": "generate_documents"})
        raise


@celery_app.task(name="find_people")
def find_people(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    run_id = workflow_run_id or workflow_runs.create("find_people", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(run_id, {"campaign_id": campaign_id, "task": "find_people", "current_step": "outreach_drafting"})
    try:
        jobs = campaign_store.list_jobs(UUID(campaign_id))
        if not jobs:
            result = {"campaign_id": campaign_id, "people_found": 0}
        else:
            context = _workflow_context(campaign_id)
            profile = context["profile"]
            if profile is None:
                result = {"campaign_id": campaign_id, "people_found": 0}
            else:
                scorer = FitScoringService()
                package_service = DocumentGeneratorService()
                people_service = PeopleFinderService()
                normalized = JobDiscoveryService.normalize(
                    Job(
                        source="campaign",
                        source_url=f"https://example.com/{jobs[0]['job_id']}",
                        title=jobs[0]["title"],
                        company=jobs[0]["company_name"],
                        remote=True,
                        required_skills=["FastAPI", "SQL"],
                    )
                )
                score = scorer.score(normalized, profile)
                package = package_service.generate_package(normalized, profile, score)
                people = people_service.find_people(package)
                result = {"campaign_id": campaign_id, "people_found": len(people)}
        workflow_runs.mark_succeeded(run_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(run_id, str(exc), {"campaign_id": campaign_id, "task": "find_people"})
        raise


@celery_app.task(name="generate_outreach")
def generate_outreach(campaign_id: str, workflow_run_id: str | None = None) -> dict[str, object]:
    run_id = workflow_run_id or workflow_runs.create("generate_outreach", {"campaign_id": campaign_id})["id"]
    workflow_runs.mark_started(run_id, {"campaign_id": campaign_id, "task": "generate_outreach", "current_step": "review_queue"})
    try:
        jobs = campaign_store.list_jobs(UUID(campaign_id))
        if not jobs:
            result = {"campaign_id": campaign_id, "drafts_created": 0}
        else:
            context = _workflow_context(campaign_id)
            profile = context["profile"]
            if profile is None:
                result = {"campaign_id": campaign_id, "drafts_created": 0}
            else:
                scorer = FitScoringService()
                package_service = DocumentGeneratorService()
                people_service = PeopleFinderService()
                email_service = EmailDiscoveryService()
                outreach_service = OutreachGeneratorService()
                review_service = ReviewQueueService()
                normalized = JobDiscoveryService.normalize(
                    Job(
                        source="campaign",
                        source_url=f"https://example.com/{jobs[0]['job_id']}",
                        title=jobs[0]["title"],
                        company=jobs[0]["company_name"],
                        remote=True,
                        required_skills=["FastAPI", "SQL"],
                    )
                )
                score = scorer.score(normalized, profile)
                package = package_service.generate_package(normalized, profile, score)
                people = people_service.find_people(package)
                candidate = email_service.generate_candidates(
                    PersonCandidate(
                        person_id=people[0].person_id,
                        company=people[0].company,
                        name=people[0].name,
                        title=people[0].title,
                        person_type=people[0].person_type,
                        source_url=people[0].source_url,
                        source_type=people[0].source_type,
                        email="jane.doe@example.com",
                        email_verification_status="verified",
                        confidence=people[0].confidence,
                        why_relevant=people[0].why_relevant,
                    ),
                    "example.com",
                )[0]
                draft = outreach_service.generate(
                    package,
                    PersonCandidate(
                        person_id=candidate.person_id,
                        company=people[0].company,
                        name=people[0].name,
                        title=people[0].title,
                        person_type=people[0].person_type,
                        source_url=people[0].source_url,
                        source_type=people[0].source_type,
                        email=candidate.email,
                        email_verification_status=candidate.verification_status,
                        confidence=people[0].confidence,
                        why_relevant=people[0].why_relevant,
                    ),
                )
                review_service.create_review("system", "outreach_draft", draft.outreach_draft_id, "2026-05-23T00:00:00Z")
                result = {"campaign_id": campaign_id, "drafts_created": 1}
        workflow_runs.mark_succeeded(run_id, result)
        return result
    except Exception as exc:  # noqa: BLE001
        workflow_runs.mark_failed(run_id, str(exc), {"campaign_id": campaign_id, "task": "generate_outreach"})
        raise
