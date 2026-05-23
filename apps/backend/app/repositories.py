from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from apps.backend.app.models import CampaignRow, CareerProfileRow
from apps.backend.app.persistence import session_scope
from apps.backend.app.modules.career_vault.models import CareerProfile
from apps.backend.app.modules.campaign_planner.models import Campaign


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CareerProfileRepository:
    def get(self, candidate_profile_id: UUID) -> CareerProfile | None:
        with session_scope() as session:
            row = session.get(CareerProfileRow, str(candidate_profile_id))
            if row is None:
                return None
            return CareerProfile.model_validate(row.profile_json)

    def upsert(self, profile: CareerProfile, upload_key: str) -> CareerProfile:
        with session_scope() as session:
            row = session.get(CareerProfileRow, str(profile.candidate_profile_id))
            if row is None:
                row = CareerProfileRow(
                    candidate_profile_id=str(profile.candidate_profile_id),
                    upload_key=upload_key,
                    profile_json=profile.model_dump(mode="json"),
                    created_at=profile.created_at,
                    updated_at=profile.updated_at,
                )
                session.add(row)
            else:
                row.upload_key = upload_key
                row.profile_json = profile.model_dump(mode="json")
                row.updated_at = profile.updated_at
            return profile

    def find_by_upload_key(self, upload_key: str) -> CareerProfile | None:
        with session_scope() as session:
            stmt = select(CareerProfileRow).where(CareerProfileRow.upload_key == upload_key)
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                return None
            return CareerProfile.model_validate(row.profile_json)


@dataclass
class CampaignRepository:
    def get(self, campaign_id: UUID) -> Campaign | None:
        with session_scope() as session:
            row = session.get(CampaignRow, str(campaign_id))
            if row is None:
                return None
            return Campaign.model_validate(row.campaign_json)

    def upsert(self, campaign: Campaign) -> Campaign:
        with session_scope() as session:
            row = session.get(CampaignRow, str(campaign.campaign_id))
            payload = campaign.model_dump(mode="json")
            if row is None:
                row = CampaignRow(
                    campaign_id=str(campaign.campaign_id),
                    campaign_json=payload,
                    created_at=campaign.created_at,
                    updated_at=campaign.updated_at,
                )
                session.add(row)
            else:
                row.campaign_json = payload
                row.updated_at = campaign.updated_at
            return campaign

