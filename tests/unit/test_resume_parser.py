from __future__ import annotations

from pathlib import Path

from apps.backend.app.modules.career_vault.service import store


def test_resume_parser_builds_profile_from_text_fixture() -> None:
    text = Path("tests/fixtures/sample_resume_ai_consultant.txt").read_text(encoding="utf-8")
    result = store.parse_resume_text(text, filename="sample_resume_ai_consultant.txt")

    assert result.parse_status == "parsed"
    assert result.created_profile.full_name == "Sam Patel"
    assert "AI automation" in [skill.skill_name for skill in result.created_profile.skills]
    assert result.created_profile.approved_claims

