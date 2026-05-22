from __future__ import annotations

from apps.backend.app.modules.campaign_planner.models import CampaignCreateInput
from apps.backend.app.modules.campaign_planner.service import CampaignPlannerStore


def test_campaign_parser_converts_vague_instruction_to_structured_query() -> None:
    store = CampaignPlannerStore()
    campaign = store.create_campaign(
        CampaignCreateInput(
            natural_language_prompt="Apply to top technology companies across the USA where I fit.",
            campaign_name=None,
        )
    )

    assert campaign.status == "created"
    assert campaign.structured_query.target_countries == ["United States"]
    assert "Technology" in campaign.structured_query.company_types
    assert campaign.structured_query.minimum_fit_score >= 75
    assert campaign.execution_mode == "approval_required"

