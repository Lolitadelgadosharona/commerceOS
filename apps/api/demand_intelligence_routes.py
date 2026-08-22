from typing import Annotated
from uuid import UUID

from commerce_os.intelligence.demand_bridge_models import (
    DemandSignal,
    DemandSignalEvidence,
    DemandSignalSource,
)
from commerce_os.intelligence.demand_bridge_schemas import (
    BusinessDemandSignalCreate,
    DemandAggregationCreate,
    DemandDashboardRead,
    DemandSignalEvidenceRead,
    DemandSignalRead,
    DemandSignalSourceCreate,
    DemandSignalSourceRead,
    DemandSignalTransition,
)
from commerce_os.intelligence.demand_bridge_services import (
    DemandIntelligenceService,
)
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.market_connector_routes import initiating_actor

router = APIRouter()


def _actor_id(request: Request) -> UUID:
    actor = initiating_actor(request)
    if actor is None:
        raise ApiError(401, "actor_required", "Verified actor identity is required.")
    return actor


@router.post("/demand-sources", response_model=DemandSignalSourceRead, status_code=201)
def create_demand_source(
    payload: DemandSignalSourceCreate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> DemandSignalSource:
    return DemandIntelligenceService(session).create_source(payload, _actor_id(request))


@router.get("/demand-sources", response_model=list[DemandSignalSourceRead])
def list_demand_sources(
    organization_id: Annotated[UUID, Query()],
    session: Annotated[Session, Depends(get_session)],
) -> list[DemandSignalSource]:
    return list(
        session.scalars(
            select(DemandSignalSource)
            .where(DemandSignalSource.organization_id == organization_id)
            .order_by(DemandSignalSource.source_type)
        )
    )


@router.post("/demand-signals/ingest", response_model=DemandSignalRead, status_code=201)
def ingest_business_demand_signal(
    payload: BusinessDemandSignalCreate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> DemandSignal:
    return DemandIntelligenceService(session).ingest(payload, _actor_id(request))


@router.post("/demand-signals", response_model=DemandSignalRead, status_code=201)
def create_demand_signal(
    payload: DemandAggregationCreate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> DemandSignal:
    return DemandIntelligenceService(session).aggregate(payload, _actor_id(request))


@router.get("/demand-signals", response_model=list[DemandSignalRead])
def list_demand_signals(
    organization_id: Annotated[UUID, Query()],
    session: Annotated[Session, Depends(get_session)],
) -> list[DemandSignal]:
    return list(
        session.scalars(
            select(DemandSignal)
            .where(DemandSignal.organization_id == organization_id)
            .order_by(DemandSignal.created_at.desc())
        )
    )


@router.patch("/demand-signals/{signal_id}", response_model=DemandSignalRead)
def review_demand_signal(
    signal_id: UUID,
    organization_id: Annotated[UUID, Query()],
    payload: DemandSignalTransition,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> DemandSignal:
    service = DemandIntelligenceService(session)
    entity = service.scoped(DemandSignal, signal_id, organization_id)
    return service.transition(
        entity, payload.status, payload.approval_request_id, _actor_id(request)
    )


@router.get("/demand-signal-evidence", response_model=list[DemandSignalEvidenceRead])
def list_demand_signal_evidence(
    organization_id: Annotated[UUID, Query()],
    session: Annotated[Session, Depends(get_session)],
    demand_signal_id: Annotated[UUID | None, Query()] = None,
) -> list[DemandSignalEvidence]:
    statement = select(DemandSignalEvidence).where(
        DemandSignalEvidence.organization_id == organization_id
    )
    if demand_signal_id is not None:
        DemandIntelligenceService(session).scoped(DemandSignal, demand_signal_id, organization_id)
        statement = statement.where(DemandSignalEvidence.demand_signal_id == demand_signal_id)
    return list(session.scalars(statement.order_by(DemandSignalEvidence.created_at)))


@router.get("/demand-intelligence-dashboard", response_model=DemandDashboardRead)
def demand_intelligence_dashboard(
    organization_id: Annotated[UUID, Query()],
    session: Annotated[Session, Depends(get_session)],
) -> DemandDashboardRead:
    return DemandIntelligenceService(session).dashboard(organization_id)
