from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.intelligence.errors import IntelligenceNotFoundError
from commerce_os.intelligence.models import (
    CustomerInsight,
    CustomerSignal,
    CustomerVoiceCluster,
    InsightStatus,
    SignalSource,
)
from commerce_os.intelligence.schemas import (
    CustomerInsightCreate,
    CustomerInsightRead,
    CustomerInsightUpdate,
    CustomerSignalCreate,
    CustomerSignalRead,
    CustomerVoiceClusterCreate,
    CustomerVoiceClusterRead,
    SignalSourceCreate,
    SignalSourceRead,
    SignalSourceUpdate,
)
from commerce_os.intelligence.services import ClusterService, InsightService, SignalService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _get_or_raise(session: Session, model: type[ModelT], entity_id: UUID) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise IntelligenceNotFoundError("The requested intelligence resource was not found.")
    return entity


@router.post(
    "/signal-sources", response_model=SignalSourceRead, status_code=201, tags=["signal_sources"]
)
def create_signal_source(payload: SignalSourceCreate, session: SessionDependency) -> SignalSource:
    source = SignalSource(**payload.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.get("/signal-sources", response_model=list[SignalSourceRead], tags=["signal_sources"])
def list_signal_sources(organization_id: UUID, session: SessionDependency) -> list[SignalSource]:
    return list(
        session.scalars(
            select(SignalSource)
            .where(SignalSource.organization_id == organization_id)
            .order_by(SignalSource.created_at.desc())
        )
    )


@router.get("/signal-sources/{source_id}", response_model=SignalSourceRead, tags=["signal_sources"])
def get_signal_source(source_id: UUID, session: SessionDependency) -> SignalSource:
    return _get_or_raise(session, SignalSource, source_id)


@router.patch(
    "/signal-sources/{source_id}", response_model=SignalSourceRead, tags=["signal_sources"]
)
def update_signal_source(
    source_id: UUID, payload: SignalSourceUpdate, session: SessionDependency
) -> SignalSource:
    source = _get_or_raise(session, SignalSource, source_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    session.commit()
    session.refresh(source)
    return source


@router.post(
    "/customer-signals",
    response_model=CustomerSignalRead,
    status_code=201,
    tags=["customer_signals"],
)
def create_customer_signal(
    payload: CustomerSignalCreate, session: SessionDependency
) -> CustomerSignal:
    return SignalService(session).create(payload)


@router.get("/customer-signals", response_model=list[CustomerSignalRead], tags=["customer_signals"])
def list_customer_signals(
    organization_id: UUID,
    session: SessionDependency,
    customer_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[CustomerSignal]:
    statement = select(CustomerSignal).where(CustomerSignal.organization_id == organization_id)
    if customer_id is not None:
        statement = statement.where(CustomerSignal.customer_id == customer_id)
    return list(session.scalars(statement.order_by(CustomerSignal.created_at.desc()).limit(limit)))


@router.get(
    "/customer-signals/{signal_id}",
    response_model=CustomerSignalRead,
    tags=["customer_signals"],
)
def get_customer_signal(signal_id: UUID, session: SessionDependency) -> CustomerSignal:
    return _get_or_raise(session, CustomerSignal, signal_id)


@router.post(
    "/customer-clusters",
    response_model=CustomerVoiceClusterRead,
    status_code=201,
    tags=["customer_clusters"],
)
def create_customer_cluster(
    payload: CustomerVoiceClusterCreate, session: SessionDependency
) -> CustomerVoiceCluster:
    return ClusterService(session).create(payload)


@router.get(
    "/customer-clusters",
    response_model=list[CustomerVoiceClusterRead],
    tags=["customer_clusters"],
)
def list_customer_clusters(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerVoiceCluster]:
    return list(
        session.scalars(
            select(CustomerVoiceCluster)
            .where(CustomerVoiceCluster.organization_id == organization_id)
            .order_by(CustomerVoiceCluster.created_at.desc())
        )
    )


@router.get(
    "/customer-clusters/{cluster_id}",
    response_model=CustomerVoiceClusterRead,
    tags=["customer_clusters"],
)
def get_customer_cluster(cluster_id: UUID, session: SessionDependency) -> CustomerVoiceCluster:
    return _get_or_raise(session, CustomerVoiceCluster, cluster_id)


@router.post(
    "/customer-insights",
    response_model=CustomerInsightRead,
    status_code=201,
    tags=["customer_insights"],
)
def create_customer_insight(
    payload: CustomerInsightCreate, session: SessionDependency
) -> CustomerInsight:
    return InsightService(session).create(payload)


@router.get(
    "/customer-insights",
    response_model=list[CustomerInsightRead],
    tags=["customer_insights"],
)
def list_customer_insights(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerInsight]:
    return list(
        session.scalars(
            select(CustomerInsight)
            .where(CustomerInsight.organization_id == organization_id)
            .order_by(CustomerInsight.created_at.desc())
        )
    )


@router.get(
    "/customer-insights/{insight_id}",
    response_model=CustomerInsightRead,
    tags=["customer_insights"],
)
def get_customer_insight(insight_id: UUID, session: SessionDependency) -> CustomerInsight:
    return _get_or_raise(session, CustomerInsight, insight_id)


@router.patch(
    "/customer-insights/{insight_id}",
    response_model=CustomerInsightRead,
    tags=["customer_insights"],
)
def update_customer_insight(
    insight_id: UUID, payload: CustomerInsightUpdate, session: SessionDependency
) -> CustomerInsight:
    return InsightService(session).update_status(insight_id, InsightStatus(payload.status))
