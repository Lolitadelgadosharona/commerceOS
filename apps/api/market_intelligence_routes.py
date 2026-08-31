from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.market_models import (
    MarketDataSource,
    MarketSignal,
    MarketSignalCluster,
    MarketSignalClusterMembership,
    MarketSignalEvidence,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.market_schemas import (
    ClusterMembershipCreate,
    ClusterMembershipRead,
    ClusterSignalProjection,
    MarketClusterCreate,
    MarketClusterRead,
    MarketEvidenceCreate,
    MarketEvidenceRead,
    MarketSignalCreate,
    MarketSignalRead,
    MarketSignalUpdate,
    MarketSourceCreate,
    MarketSourceRead,
    MarketSourceUpdate,
    OpportunityLinkCreate,
    OpportunityLinkRead,
    SignalOpportunityProjection,
)
from commerce_os.intelligence.market_services import MarketIntelligenceService, scoped_market
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped_model = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped_model.organization_id == organization_id)
            .order_by(mapped_model.created_at.desc())
        )
    )


@router.post("/market-sources", response_model=MarketSourceRead, status_code=201)
def create_source(payload: MarketSourceCreate, session: SessionDependency) -> MarketDataSource:
    return MarketIntelligenceService(session).create_source(payload)


@router.get("/market-sources", response_model=list[MarketSourceRead])
def list_sources(organization_id: UUID, session: SessionDependency) -> list[MarketDataSource]:
    return _list(session, MarketDataSource, organization_id)


@router.patch("/market-sources/{source_id}", response_model=MarketSourceRead)
def transition_source(
    source_id: UUID,
    organization_id: UUID,
    payload: MarketSourceUpdate,
    session: SessionDependency,
) -> MarketDataSource:
    source = scoped_market(session, MarketDataSource, source_id, organization_id)
    return MarketIntelligenceService(session).transition_source(source, payload.status)


@router.post("/market-signals", response_model=MarketSignalRead, status_code=201)
def create_signal(payload: MarketSignalCreate, session: SessionDependency) -> MarketSignal:
    return MarketIntelligenceService(session).create_signal(payload)


@router.get("/market-signals", response_model=list[MarketSignalRead])
def list_signals(organization_id: UUID, session: SessionDependency) -> list[MarketSignal]:
    return _list(session, MarketSignal, organization_id)


@router.patch("/market-signals/{signal_id}", response_model=MarketSignalRead)
def transition_signal(
    signal_id: UUID,
    organization_id: UUID,
    payload: MarketSignalUpdate,
    session: SessionDependency,
) -> MarketSignal:
    signal = scoped_market(session, MarketSignal, signal_id, organization_id)
    return MarketIntelligenceService(session).transition_signal(signal, payload.status)


@router.post("/market-evidence", response_model=MarketEvidenceRead, status_code=201)
def create_evidence(
    payload: MarketEvidenceCreate, session: SessionDependency
) -> MarketSignalEvidence:
    return MarketIntelligenceService(session).add_evidence(payload)


@router.get("/market-evidence", response_model=list[MarketEvidenceRead])
def list_evidence(organization_id: UUID, session: SessionDependency) -> list[MarketSignalEvidence]:
    return _list(session, MarketSignalEvidence, organization_id)


@router.post("/market-clusters", response_model=MarketClusterRead, status_code=201)
def create_cluster(payload: MarketClusterCreate, session: SessionDependency) -> MarketSignalCluster:
    return MarketIntelligenceService(session).create_cluster(payload)


@router.get("/market-clusters", response_model=list[MarketClusterRead])
def list_clusters(organization_id: UUID, session: SessionDependency) -> list[MarketSignalCluster]:
    return _list(session, MarketSignalCluster, organization_id)


@router.post(
    "/market-clusters/{cluster_id}/signals", response_model=ClusterMembershipRead, status_code=201
)
def add_cluster_signal(
    cluster_id: UUID, payload: ClusterMembershipCreate, session: SessionDependency
) -> MarketSignalClusterMembership:
    return MarketIntelligenceService(session).add_to_cluster(
        cluster_id, payload.signal_id, payload.organization_id
    )


@router.post(
    "/market-signals/{signal_id}/opportunities",
    response_model=OpportunityLinkRead,
    status_code=201,
)
def link_opportunity(
    signal_id: UUID, payload: OpportunityLinkCreate, session: SessionDependency
) -> MarketSignalOpportunityLink:
    return MarketIntelligenceService(session).link_opportunity(
        signal_id, payload.opportunity_id, payload.organization_id
    )


@router.get(
    "/market-signals/{signal_id}/opportunities",
    response_model=list[SignalOpportunityProjection],
)
def list_signal_opportunities(
    signal_id: UUID, organization_id: UUID, session: SessionDependency
) -> list[SignalOpportunityProjection]:
    scoped_market(session, MarketSignal, signal_id, organization_id)
    statement = (
        select(MarketSignalOpportunityLink, MarketOpportunity)
        .join(MarketOpportunity, MarketOpportunity.id == MarketSignalOpportunityLink.opportunity_id)
        .where(
            MarketSignalOpportunityLink.organization_id == organization_id,
            MarketSignalOpportunityLink.signal_id == signal_id,
            MarketOpportunity.organization_id == organization_id,
        )
        .order_by(MarketSignalOpportunityLink.created_at)
    )
    return [
        SignalOpportunityProjection(
            link_id=link.id,
            signal_id=link.signal_id,
            opportunity_id=opportunity.id,
            linked_at=link.created_at,
            opportunity=opportunity,
        )
        for link, opportunity in session.execute(statement)
    ]


@router.get(
    "/market-clusters/{cluster_id}/signals",
    response_model=list[ClusterSignalProjection],
)
def list_cluster_signals(
    cluster_id: UUID, organization_id: UUID, session: SessionDependency
) -> list[ClusterSignalProjection]:
    scoped_market(session, MarketSignalCluster, cluster_id, organization_id)
    memberships = list(
        session.scalars(
            select(MarketSignalClusterMembership)
            .where(
                MarketSignalClusterMembership.organization_id == organization_id,
                MarketSignalClusterMembership.cluster_id == cluster_id,
            )
            .order_by(MarketSignalClusterMembership.created_at)
        )
    )
    projections: list[ClusterSignalProjection] = []
    for membership in memberships:
        signal = scoped_market(session, MarketSignal, membership.signal_id, organization_id)
        evidence = list(
            session.scalars(
                select(MarketSignalEvidence)
                .where(
                    MarketSignalEvidence.organization_id == organization_id,
                    MarketSignalEvidence.signal_id == signal.id,
                )
                .order_by(MarketSignalEvidence.captured_at)
            )
        )
        projections.append(
            ClusterSignalProjection(
                membership_id=membership.id,
                cluster_id=cluster_id,
                signal=signal,
                evidence=evidence,
            )
        )
    return projections
