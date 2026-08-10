from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.governance.models import AuditLog
from commerce_os.shared.models import utc_now


class AuditService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        organization_id: UUID,
        actor_type: str,
        actor_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=utc_now(),
            event_metadata=metadata or {},
        )
        self.session.add(log)
        return log

    def list(self, *, organization_id: UUID, limit: int = 100) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))
