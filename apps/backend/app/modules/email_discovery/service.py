from __future__ import annotations

from dataclasses import dataclass

from apps.backend.app.modules.people_finder.service import EmailCandidate, PersonCandidate


@dataclass(frozen=True)
class VerificationResult:
    status: str
    score: float
    verified_at: str | None


class EmailVerificationAdapter:
    def verify(self, email: str) -> VerificationResult:
        local_part = email.split("@", 1)[0]
        if "." in local_part:
            return VerificationResult("verified", 0.95, "2026-05-21T00:00:00Z")
        return VerificationResult("unverified", 0.2, None)


class EmailDiscoveryService:
    def __init__(self, verifier: EmailVerificationAdapter | None = None) -> None:
        self.verifier = verifier or EmailVerificationAdapter()
        self.candidates: dict[str, list[EmailCandidate]] = {}

    def generate_candidates(self, person: PersonCandidate, domain: str) -> list[EmailCandidate]:
        local_parts = [
            f"{person.name.lower().replace(' ', '.')}",
            f"{person.name.lower().replace(' ', '')}",
        ]
        candidates: list[EmailCandidate] = []
        for local in local_parts:
            email = f"{local}@{domain}"
            verification = self.verifier.verify(email)
            candidates.append(
                EmailCandidate(
                    email_candidate_id=f"email-{person.person_id}-{local}",
                    person_id=person.person_id,
                    email=email,
                    generation_method="pattern_first_last",
                    source_domain=domain,
                    verification_status=verification.status,
                    verification_score=verification.score,
                    verified_at=verification.verified_at,
                )
            )
        ranked = sorted(candidates, key=lambda item: item.verification_score, reverse=True)
        self.candidates[person.person_id] = ranked
        return ranked

    def best_candidate(self, person_id: str) -> EmailCandidate | None:
        candidates = self.candidates.get(person_id, [])
        return candidates[0] if candidates else None
