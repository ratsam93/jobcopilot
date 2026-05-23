from __future__ import annotations

from dataclasses import asdict, dataclass, field

from apps.backend.app.modules.fit_scoring.service import CandidateProfile, JobScore
from apps.backend.app.modules.job_discovery.service import NormalizedJob
from apps.backend.app.persistence_repos import ApplicationPackageRepository
from apps.backend.app.shared.contracts import ResumeTailoringResult, CoverLetterResult


@dataclass(frozen=True)
class ResumeVersion:
    resume_version_id: str
    version_number: int
    resume_text: str
    change_log: list[dict[str, str]]
    unsupported_claims_detected: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApplicationPackage:
    application_package_id: str
    job_id: str
    candidate_profile_id: str
    fit_summary: list[str]
    unsupported_claims_detected: list[str]
    risk_flags: list[str]
    status: str
    resume_version: ResumeVersion
    cover_letter: str


class DocumentGeneratorService:
    def __init__(self) -> None:
        self.repo = ApplicationPackageRepository()

    def generate_package(self, job: NormalizedJob, profile: CandidateProfile, score: JobScore) -> ApplicationPackage:
        unsupported = [claim for claim in job.required_skills if claim.lower() in {item.lower() for item in profile.do_not_claim}]
        change_log = [
            {
                "section": "Summary",
                "change_type": "reordered",
                "description": f"Opened with {profile.target_roles[0] if profile.target_roles else 'approved experience'} for {job.title}.",
            }
        ]
        if score.matched_skills:
            change_log.append(
                {
                    "section": "Skills",
                    "change_type": "keyword_alignment",
                    "description": f"Aligned to approved skills: {', '.join(score.matched_skills)}.",
                }
            )
        resume_version = ResumeVersion(
            resume_version_id=f"resume-{job.job_id}",
            version_number=1,
            resume_text=self._resume_text(job, profile, score),
            change_log=change_log,
            unsupported_claims_detected=unsupported,
        )
        status = "review_pending"
        package = ApplicationPackage(
            application_package_id=f"pkg-{job.job_id}",
            job_id=job.job_id,
            candidate_profile_id=profile.candidate_profile_id,
            fit_summary=self._fit_summary(job, profile, score),
            unsupported_claims_detected=unsupported,
            risk_flags=score.risk_flags,
            status=status,
            resume_version=resume_version,
            cover_letter=self._cover_letter(job, profile, score),
        )
        ResumeTailoringResult.model_validate(asdict(package))
        CoverLetterResult.model_validate(
            {
                "subject": f"Application for {job.title}",
                "body": package.cover_letter,
                "personalization_points": package.fit_summary[:2],
            }
        )
        self.repo.upsert(package.application_package_id, asdict(package))
        return package

    def get(self, application_package_id: str) -> ApplicationPackage:
        payload = self.repo.get(application_package_id)
        if payload is None:
            raise KeyError(application_package_id)
        resume_version_payload = payload.get("resume_version")
        if isinstance(resume_version_payload, dict):
            payload = {**payload, "resume_version": ResumeVersion(**resume_version_payload)}
        return ApplicationPackage(**payload)

    def _fit_summary(self, job: NormalizedJob, profile: CandidateProfile, score: JobScore) -> list[str]:
        base = [f"Target role match for {job.title} at {job.company}."]
        if profile.approved_skills:
            base.append(f"Approved skills available: {', '.join(profile.approved_skills[:3])}.")
        if score.risk_flags:
            base.append(f"Review risks: {', '.join(score.risk_flags)}.")
        return base

    def _resume_text(self, job: NormalizedJob, profile: CandidateProfile, score: JobScore) -> str:
        return f"{profile.full_name}\nTargeting {job.title} at {job.company}\nMatched skills: {', '.join(score.matched_skills) or 'none'}"

    def _cover_letter(self, job: NormalizedJob, profile: CandidateProfile, score: JobScore) -> str:
        return (
            f"Hello hiring team,\n\n"
            f"I am applying for the {job.title} role at {job.company}. "
            f"My background aligns through {', '.join(score.matched_skills) or 'relevant experience'}.\n"
        )
