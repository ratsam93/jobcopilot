from __future__ import annotations

from dataclasses import dataclass, field

from apps.backend.app.modules.job_discovery.service import NormalizedJob


@dataclass(frozen=True)
class CandidateProfile:
    candidate_profile_id: str
    full_name: str
    primary_email: str
    location: str
    timezone: str
    target_roles: list[str] = field(default_factory=list)
    target_geographies: list[str] = field(default_factory=list)
    salary_min_usd: int | None = None
    remote_preference: str | None = None
    approved_skills: list[str] = field(default_factory=list)
    approved_claims: list[str] = field(default_factory=list)
    do_not_claim: list[str] = field(default_factory=list)
    career_story: str = ""


@dataclass(frozen=True)
class JobScore:
    job_score_id: str
    job_id: str
    candidate_profile_id: str
    fit_score: int
    decision: str
    component_scores: dict[str, int]
    matched_skills: list[str]
    missing_skills: list[str]
    risk_flags: list[str]
    explanation: str
    confidence: float


class FitScoringService:
    def __init__(self) -> None:
        self.scores: dict[str, JobScore] = {}

    def score(self, job: NormalizedJob, profile: CandidateProfile) -> JobScore:
        role_match = self._score_role_match(job, profile)
        skill_match, matched_skills, missing_skills = self._score_skill_match(job, profile)
        seniority_match = 12 if any(term in job.title.lower() for term in self._role_terms(profile)) else 8
        location_match, risk_flags = self._score_location(job, profile)
        salary_business_value = 8 if self._salary_ok(job, profile) else 4
        company_quality = 4 if job.company else 0
        internal_outreach_potential = 3 if job.remote or "manager" in job.title.lower() else 2

        component_scores = {
            "role_match": role_match,
            "skill_match": skill_match,
            "seniority_match": seniority_match,
            "location_match": location_match,
            "salary_business_value": salary_business_value,
            "company_quality": company_quality,
            "internal_outreach_potential": internal_outreach_potential,
        }
        fit_score = min(100, sum(component_scores.values()))
        decision = self._decision(fit_score)
        explanation = self._explanation(job, matched_skills, missing_skills, risk_flags)
        confidence = round(min(0.95, 0.5 + fit_score / 200), 2)
        result = JobScore(
            job_score_id=f"score-{job.job_id}",
            job_id=job.job_id,
            candidate_profile_id=profile.candidate_profile_id,
            fit_score=fit_score,
            decision=decision,
            component_scores=component_scores,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            risk_flags=risk_flags,
            explanation=explanation,
            confidence=confidence,
        )
        self.scores[result.job_score_id] = result
        return result

    def get(self, job_score_id: str) -> JobScore:
        return self.scores[job_score_id]

    def _role_terms(self, profile: CandidateProfile) -> list[str]:
        return [role.lower() for role in profile.target_roles]

    def _score_role_match(self, job: NormalizedJob, profile: CandidateProfile) -> int:
        title = job.title.lower()
        for role in self._role_terms(profile):
            if role and role in title:
                return 25
        return 15

    def _score_skill_match(self, job: NormalizedJob, profile: CandidateProfile) -> tuple[int, list[str], list[str]]:
        required = [skill.lower() for skill in job.required_skills]
        approved = [skill.lower() for skill in profile.approved_skills]
        matched = [skill for skill in job.required_skills if skill.lower() in approved]
        missing = [skill for skill in job.required_skills if skill.lower() not in approved]
        if not required:
            return 15, [], []
        ratio = len(matched) / len(required)
        return int(round(25 * ratio)), matched, missing

    def _score_location(self, job: NormalizedJob, profile: CandidateProfile) -> tuple[int, list[str]]:
        risk_flags: list[str] = []
        if job.remote:
            return 15, risk_flags
        if job.location and profile.location.lower() in job.location.lower():
            return 15, risk_flags
        if "required" in (profile.remote_preference or "").lower():
            risk_flags.append("location mismatch")
        return 6, risk_flags

    def _salary_ok(self, job: NormalizedJob, profile: CandidateProfile) -> bool:
        if profile.salary_min_usd is None or job.salary_max_usd is None:
            return True
        return job.salary_max_usd >= profile.salary_min_usd

    def _decision(self, fit_score: int) -> str:
        if fit_score >= 85:
            return "generate_application_package"
        if fit_score >= 70:
            return "prepare_for_review"
        if fit_score >= 55:
            return "save_for_later"
        return "reject"

    def _explanation(self, job: NormalizedJob, matched_skills: list[str], missing_skills: list[str], risk_flags: list[str]) -> str:
        parts = [f"Role alignment for {job.title} at {job.company}."]
        if matched_skills:
            parts.append(f"Matched skills: {', '.join(matched_skills)}.")
        if missing_skills:
            parts.append(f"Missing skills: {', '.join(missing_skills)}.")
        if risk_flags:
            parts.append(f"Risk flags: {', '.join(risk_flags)}.")
        return " ".join(parts)
