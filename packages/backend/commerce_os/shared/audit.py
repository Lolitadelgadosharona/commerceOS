from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert
from sqlalchemy.orm import Session

from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now


def record_audit_event(
    session: Session,
    *,
    organization_id: UUID,
    actor_type: str,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist through the Governance-owned audit table without a domain import."""
    now = utc_now()
    session.execute(
        insert(Base.metadata.tables["audit_logs"]).values(
            id=uuid4(),
            organization_id=organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=now,
            metadata=metadata or {},
        )
    )
