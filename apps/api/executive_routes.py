from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.executive_models import (
    ExecutiveMetricSnapshot,
    OperatingCommitteeReview,
    OperatingSignal,
)
from commerce_os.decision.executive_schemas import (
    ExecutiveMetricCreate,
    ExecutiveMetricRead,
    OperatingReviewCreate,
    OperatingReviewRead,
    OperatingReviewUpdate,
    OperatingSignalCreate,
    OperatingSignalRead,
    OperatingSignalUpdate,
)
from commerce_os.decision.executive_services import ExecutiveDecisionService, scoped_entity
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import (
    DecisionQueueCreate,
    DecisionQueueRead,
    DecisionQueueUpdate,
)
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


class DashboardView(BaseModel):
    organization_id: UUID
    view: str
    metrics: list[ExecutiveMetricRead]
    signals: list[OperatingSignalRead]
    decisions: list[DecisionQueueRead]


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped_model = cast(Any, model)
    organization_column = mapped_model.organization_id
    created_column = mapped_model.created_at
    return list(
        session.scalars(
            select(model)
            .where(organization_column == organization_id)
            .order_by(created_column.desc())
        )
    )


@router.post("/executive-metrics", response_model=ExecutiveMetricRead, status_code=201)
def create_metric(
    payload: ExecutiveMetricCreate, session: SessionDependency
) -> ExecutiveMetricSnapshot:
    return ExecutiveDecisionService(session).create_metric(payload)


@router.get("/executive-metrics", response_model=list[ExecutiveMetricRead])
def list_metrics(
    organization_id: UUID, session: SessionDependency
) -> list[ExecutiveMetricSnapshot]:
    return _list(session, ExecutiveMetricSnapshot, organization_id)


@router.post("/operating-signals", response_model=OperatingSignalRead, status_code=201)
def create_signal(payload: OperatingSignalCreate, session: SessionDependency) -> OperatingSignal:
    return ExecutiveDecisionService(session).create_signal(payload)


@router.get("/operating-signals", response_model=list[OperatingSignalRead])
def list_signals(organization_id: UUID, session: SessionDependency) -> list[OperatingSignal]:
    return _list(session, OperatingSignal, organization_id)


@router.patch("/operating-signals/{signal_id}", response_model=OperatingSignalRead)
def transition_signal(
    signal_id: UUID,
    organization_id: UUID,
    payload: OperatingSignalUpdate,
    session: SessionDependency,
) -> OperatingSignal:
    signal = scoped_entity(session, OperatingSignal, signal_id, organization_id)
    return ExecutiveDecisionService(session).transition_signal(signal, payload.status)


@router.post("/decision-queue", response_model=DecisionQueueRead, status_code=201)
def create_decision(payload: DecisionQueueCreate, session: SessionDependency) -> DecisionQueueItem:
    return DecisionQueueService(session).create(payload)


@router.get("/decision-queue", response_model=list[DecisionQueueRead])
def list_decisions(organization_id: UUID, session: SessionDependency) -> list[DecisionQueueItem]:
    return _list(session, DecisionQueueItem, organization_id)


@router.patch("/decision-queue/{item_id}", response_model=DecisionQueueRead)
def transition_decision(
    item_id: UUID, organization_id: UUID, payload: DecisionQueueUpdate, session: SessionDependency
) -> DecisionQueueItem:
    service = DecisionQueueService(session)
    return service.transition(service.scoped(item_id, organization_id), payload.status)


@router.post("/operating-reviews", response_model=OperatingReviewRead, status_code=201)
def create_review(
    payload: OperatingReviewCreate, session: SessionDependency
) -> OperatingCommitteeReview:
    return ExecutiveDecisionService(session).create_review(payload)


@router.get("/operating-reviews", response_model=list[OperatingReviewRead])
def list_reviews(
    organization_id: UUID, session: SessionDependency
) -> list[OperatingCommitteeReview]:
    return _list(session, OperatingCommitteeReview, organization_id)


@router.patch("/operating-reviews/{review_id}", response_model=OperatingReviewRead)
def transition_review(
    review_id: UUID,
    organization_id: UUID,
    payload: OperatingReviewUpdate,
    session: SessionDependency,
) -> OperatingCommitteeReview:
    review = scoped_entity(session, OperatingCommitteeReview, review_id, organization_id)
    return ExecutiveDecisionService(session).transition_review(review, payload.status)


VIEW_METRICS = {
    "executive-overview": None,
    "need-your-decision": set(),
    "financial-health": {"revenue", "profit"},
    "product-opportunities": {"product"},
    "customer-health": {"customer"},
    "creative-performance": {"creative"},
    "channel-performance": {"channel"},
    "risk-overview": {"risk"},
}


@router.get("/dashboard/{view_name}", response_model=DashboardView)
def dashboard(view_name: str, organization_id: UUID, session: SessionDependency) -> DashboardView:
    if view_name not in VIEW_METRICS:
        from apps.api.errors import ApiError

        raise ApiError(404, "not_found", "Dashboard view was not found.")
    categories = VIEW_METRICS[view_name]
    metrics = _list(session, ExecutiveMetricSnapshot, organization_id)
    if categories is not None:
        metrics = [metric for metric in metrics if metric.metric_type in categories]
    signals = _list(session, OperatingSignal, organization_id)
    decisions = _list(session, DecisionQueueItem, organization_id)
    if view_name == "need-your-decision":
        signals = []
    elif view_name != "executive-overview" and view_name != "risk-overview":
        signals = [signal for signal in signals if signal.domain in _domains_for(view_name)]
        decisions = []
    return DashboardView(
        organization_id=organization_id,
        view=view_name,
        metrics=metrics,
        signals=signals,
        decisions=decisions,
    )


def _domains_for(view_name: str) -> set[str]:
    return {
        "financial-health": {"finance"},
        "product-opportunities": {"intelligence", "build", "decision"},
        "customer-health": {"operations", "intelligence"},
        "creative-performance": {"decision", "build"},
        "channel-performance": {"growth", "decision"},
    }.get(view_name, set())
