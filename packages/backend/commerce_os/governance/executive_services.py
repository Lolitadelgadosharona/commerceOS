from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.governance.errors import GovernanceError
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

QUEUE_TRANSITIONS = {
    "pending": {"acknowledged", "closed"},
    "acknowledged": {"closed"},
    "closed": set(),
}


class DecisionQueueService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: DecisionQueueCreate) -> DecisionQueueItem:
        table = Base.metadata.tables["organizations"]
        exists = self.session.execute(
            select(table.c.id).where(table.c.id == payload.organization_id)
        ).scalar_one_or_none()
        if exists is None:
            raise GovernanceError("not_found", "Organization was not found.")
        if payload.approval_request_id and not reference_belongs_to_organization(
            self.session,
            table_name="approval_requests",
            reference_id=payload.approval_request_id,
            organization_id=payload.organization_id,
        ):
            raise GovernanceError(
                "not_found", "Approval request was not found in this organization."
            )
        return self._save(DecisionQueueItem(**payload.model_dump(), status="pending"))

    def transition(self, item: DecisionQueueItem, status: str) -> DecisionQueueItem:
        if status not in QUEUE_TRANSITIONS[item.status]:
            raise GovernanceError(
                "invalid_state_transition",
                f"Decision queue item cannot transition from {item.status} to {status}.",
            )
        item.status = status
        return self._save(item)

    def scoped(self, item_id: UUID, organization_id: UUID) -> DecisionQueueItem:
        item = self.session.get(DecisionQueueItem, item_id)
        if item is None or item.organization_id != organization_id:
            raise GovernanceError(
                "not_found", "Decision queue item was not found in this organization."
            )
        return item

    def _save(self, item: DecisionQueueItem) -> DecisionQueueItem:
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
