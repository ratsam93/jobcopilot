from __future__ import annotations

from importlib import reload
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.backend.app import persistence
from apps.backend.app.db_init import initialize_database
from apps.backend.app.modules.career_vault.models import CareerProfile, ResumeSource
from apps.backend.app.modules.campaign_planner.models import Campaign, StructuredQuery
from apps.backend.app.modules.career_vault.service import CareerVaultStore
from apps.backend.app.modules.campaign_planner.service import CampaignPlannerStore
from apps.backend.app.persistence import Base


def _bind_sqlite(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path}", future=True)
    persistence.engine = engine
    persistence.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    initialize_database()


def test_profile_survives_restart(tmp_path: Path) -> None:
    db_file = tmp_path / "jobcopilot.db"
    _bind_sqlite(db_file)
    store = CareerVaultStore()
    profile = CareerProfile(
        full_name="Sam Patel",
        primary_email="sam@example.com",
        source_resumes=[ResumeSource(filename="resume.txt", text="Sam Patel AI automation FastAPI SQL")],
    )
    store._persist_profile(profile, "resume.txt::sam patel")

    persistence.engine.dispose()
    _bind_sqlite(db_file)
    restarted = CareerVaultStore()
    loaded = restarted.get_profile(profile.candidate_profile_id)
    assert loaded.full_name == "Sam Patel"
    assert loaded.primary_email == "sam@example.com"


def test_campaign_survives_restart(tmp_path: Path) -> None:
    db_file = tmp_path / "jobcopilot-campaign.db"
    _bind_sqlite(db_file)
    planner = CampaignPlannerStore()
    campaign = Campaign(
        campaign_id=__import__("uuid").uuid4(),
        natural_language_prompt="Apply to top tech companies",
        campaign_name="Top tech companies",
        structured_query=StructuredQuery(target_countries=["United States"], target_locations=["Remote"]),
    )
    planner._persist(campaign)

    persistence.engine.dispose()
    _bind_sqlite(db_file)
    restarted = CampaignPlannerStore()
    loaded = restarted.get_campaign(campaign.campaign_id)
    assert loaded.campaign_name == "Top tech companies"
    assert loaded.structured_query.target_countries == ["United States"]
