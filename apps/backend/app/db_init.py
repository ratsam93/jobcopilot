from sqlalchemy import inspect, text

from apps.backend.app.models import (
    ApplicationPackageRow,
    AuditLogRow,
    CampaignRow,
    CareerProfileRow,
    EmailCandidateRow,
    JobRecordRow,
    JobScoreRow,
    ModuleRegistryRow,
    OutreachDraftRow,
    PeopleCacheRow,
    ReviewItemRow,
    TrackerApplicationRow,
    WorkflowRunRow,
    UserRow,
)
from apps.backend.app import persistence
from apps.backend.app.persistence import Base


def initialize_database() -> None:
    Base.metadata.create_all(
        bind=persistence.engine,
        tables=[
            AuditLogRow.__table__,
            WorkflowRunRow.__table__,
            UserRow.__table__,
            CareerProfileRow.__table__,
            CampaignRow.__table__,
            ModuleRegistryRow.__table__,
            JobRecordRow.__table__,
            JobScoreRow.__table__,
            ApplicationPackageRow.__table__,
            OutreachDraftRow.__table__,
            ReviewItemRow.__table__,
            TrackerApplicationRow.__table__,
            EmailCandidateRow.__table__,
            PeopleCacheRow.__table__,
        ],
    )
    inspector = inspect(persistence.engine)
    existing_tables = set(inspector.get_table_names())
    if "users" not in existing_tables:
        return
    with persistence.engine.begin() as connection:
        for table, columns in {
            "audit_logs": ["user_id"],
            "workflow_runs": ["user_id", "updated_at"],
            "career_profiles": ["user_id"],
            "campaigns": ["user_id"],
            "module_registry": ["user_id"],
            "job_records": ["user_id"],
            "job_scores": ["user_id"],
            "application_packages": ["user_id"],
            "outreach_drafts": ["user_id"],
            "review_items": ["user_id"],
            "tracker_applications": ["user_id"],
            "email_candidates": ["user_id"],
            "people_cache": ["user_id"],
        }.items():
            if table not in existing_tables:
                continue
            current_columns = {column["name"] for column in inspector.get_columns(table)}
            for column in columns:
                if column not in current_columns:
                    if column == "updated_at":
                        connection.execute(
                            text(
                                f"ALTER TABLE {table} ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                            )
                        )
                    else:
                        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(36)"))
        if "outreach_drafts" in existing_tables:
            draft_columns = {column["name"] for column in inspector.get_columns("outreach_drafts")}
            if "gmail_draft_id" not in draft_columns:
                connection.execute(text("ALTER TABLE outreach_drafts ADD COLUMN gmail_draft_id VARCHAR(128)"))
            if "gmail_draft_status" not in draft_columns:
                connection.execute(text("ALTER TABLE outreach_drafts ADD COLUMN gmail_draft_status VARCHAR(50)"))


initialize_database()
