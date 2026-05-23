from apps.backend.app.models import AuditLogRow, CampaignRow, CareerProfileRow, WorkflowRunRow
from apps.backend.app.persistence import Base, engine


def initialize_database() -> None:
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AuditLogRow.__table__,
            WorkflowRunRow.__table__,
            CareerProfileRow.__table__,
            CampaignRow.__table__,
        ],
    )


initialize_database()
