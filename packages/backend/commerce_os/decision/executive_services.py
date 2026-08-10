from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.executive_models import (
    ExecutiveMetricSnapshot,
    OperatingCommitteeReview,
    OperatingSignal,
)
from commerce_os.decision.executive_schemas import (
    ExecutiveMetricCreate,
    OperatingReviewCreate,
    OperatingSignalCreate,
)
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
SIGNAL_TRANSITIONS = {
    "open": {"acknowledged", "resolved"},
    "acknowledged": {"resolved"},
    "resolved": set(),
}
REVIEW_TRANSITIONS = {"draft": {"reviewed"}, "reviewed": {"archived"}, "archived": set()}


class ExecutiveDecisionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_metric(self, payload: ExecutiveMetricCreate) -> ExecutiveMetricSnapshot:
        self._period(payload.period_id, payload.organization_id)
        return self._save(ExecutiveMetricSnapshot(**payload.model_dump()))

    def create_signal(self, payload: OperatingSignalCreate) -> OperatingSignal:
        self._organization(payload.organization_id)
        return self._save(OperatingSignal(**payload.model_dump(), status="open"))

    def transition_signal(self, signal: OperatingSignal, status: str) -> OperatingSignal:
        if status not in SIGNAL_TRANSITIONS[signal.status]:
            raise DecisionStateError(
                f"Operating signal cannot transition from {signal.status} to {status}."
            )
        signal.status = status
        return self._save(signal)

    def create_review(self, payload: OperatingReviewCreate) -> OperatingCommitteeReview:
        self._period(payload.period_id, payload.organization_id)
        return self._save(OperatingCommitteeReview(**payload.model_dump(), status="draft"))

    def transition_review(
        self, review: OperatingCommitteeReview, status: str
    ) -> OperatingCommitteeReview:
        if status not in REVIEW_TRANSITIONS[review.status]:
            raise DecisionStateError(
                f"Operating review cannot transition from {review.status} to {status}."
            )
        review.status = status
        return self._save(review)

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if (
            self.session.execute(
                select(table.c.id).where(table.c.id == organization_id)
            ).scalar_one_or_none()
            is None
        ):
            raise DecisionScopeError("Organization was not found.")

    def _period(self, period_id: UUID, organization_id: UUID) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name="financial_periods",
            reference_id=period_id,
            organization_id=organization_id,
        ):
            raise DecisionScopeError("Financial period was not found in this organization.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity


def scoped_entity(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise DecisionScopeError("Executive record was not found in this organization.")
    return entity
