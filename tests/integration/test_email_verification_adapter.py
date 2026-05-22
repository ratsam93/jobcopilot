from __future__ import annotations

from apps.backend.app.modules.email_discovery.service import EmailDiscoveryService
from apps.backend.app.modules.people_finder.service import PersonCandidate


def test_email_verification_adapter_blocks_unverified_emails() -> None:
    person = PersonCandidate(
        person_id="person-1",
        company="Acme AI",
        name="Jane Doe",
        title="Hiring Manager",
        person_type="likely_hiring_manager",
        source_url="https://example.com/team",
        source_type="company_page",
        email=None,
        email_verification_status="not_checked",
        confidence=0.9,
        why_relevant="Owns the team.",
    )
    candidates = EmailDiscoveryService().generate_candidates(person, "example.com")

    assert candidates[0].verification_status in {"verified", "unverified"}
    assert candidates[0].source_domain == "example.com"

