from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.shared.database import Base


def reference_belongs_to_organization(
    session: Session, *, table_name: str, reference_id: UUID, organization_id: UUID
) -> bool:
    """Validate a tenant-scoped reference without importing another domain's model."""
    table = Base.metadata.tables[table_name]
    statement = select(table.c.id).where(
        table.c.id == reference_id,
        table.c.organization_id == organization_id,
    )
    return session.execute(statement).scalar_one_or_none() is not None
