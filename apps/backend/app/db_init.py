from apps.backend.app.models import AuditLogRow, WorkflowRunRow
from apps.backend.app.persistence import Base, engine


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine, tables=[AuditLogRow.__table__, WorkflowRunRow.__table__])
