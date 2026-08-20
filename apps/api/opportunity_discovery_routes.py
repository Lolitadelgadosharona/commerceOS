from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.intelligence.discovery_models import OpportunityCandidate, OpportunityDiscoveryRun
from commerce_os.intelligence.discovery_schemas import (
    DiscoveryTemplateRead,
    OpportunityCandidateRead,
    OpportunityDiscoveryRunCreate,
    OpportunityDiscoveryRunRead,
)
from commerce_os.intelligence.discovery_services import (
    OpportunityDiscoveryService,
    scoped_discovery,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.market_connector_routes import initiating_actor

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def actor_id(request: Request) -> UUID:
    actor = initiating_actor(request)
    if actor is None:
        raise ApiError(401, "actor_required", "Verified actor identity is required.")
    return actor


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.get("/opportunity-discovery-templates", response_model=list[DiscoveryTemplateRead])
def templates() -> list[DiscoveryTemplateRead]:
    return OpportunityDiscoveryService.templates()


@router.post(
    "/opportunity-discovery-runs", response_model=OpportunityDiscoveryRunRead, status_code=201
)
def create_run(
    payload: OpportunityDiscoveryRunCreate, request: Request, session: SessionDependency
) -> OpportunityDiscoveryRun:
    return OpportunityDiscoveryService(session).create_run(payload, actor_id(request))


@router.get("/opportunity-discovery-runs", response_model=list[OpportunityDiscoveryRunRead])
def list_runs(organization_id: UUID, session: SessionDependency) -> list[OpportunityDiscoveryRun]:
    return _list(session, OpportunityDiscoveryRun, organization_id)


@router.get("/opportunity-discovery-runs/{run_id}", response_model=OpportunityDiscoveryRunRead)
def get_run(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> OpportunityDiscoveryRun:
    return scoped_discovery(session, OpportunityDiscoveryRun, run_id, organization_id)


@router.post(
    "/opportunity-discovery-runs/{run_id}/queue", response_model=OpportunityDiscoveryRunRead
)
def queue_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> OpportunityDiscoveryRun:
    service = OpportunityDiscoveryService(session)
    return service.queue(
        scoped_discovery(session, OpportunityDiscoveryRun, run_id, organization_id),
        actor_id(request),
    )


@router.post(
    "/opportunity-discovery-runs/{run_id}/cancel", response_model=OpportunityDiscoveryRunRead
)
def cancel_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> OpportunityDiscoveryRun:
    service = OpportunityDiscoveryService(session)
    return service.cancel(
        scoped_discovery(session, OpportunityDiscoveryRun, run_id, organization_id),
        actor_id(request),
    )


@router.get("/opportunity-candidates", response_model=list[OpportunityCandidateRead])
def list_candidates(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityCandidate]:
    return _list(session, OpportunityCandidate, organization_id)


@router.get("/opportunity-candidates/{candidate_id}", response_model=OpportunityCandidateRead)
def get_candidate(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> OpportunityCandidate:
    return scoped_discovery(session, OpportunityCandidate, candidate_id, organization_id)


@router.post(
    "/opportunity-candidates/{candidate_id}/review", response_model=OpportunityCandidateRead
)
def review_candidate(
    candidate_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> OpportunityCandidate:
    service = OpportunityDiscoveryService(session)
    candidate = scoped_discovery(session, OpportunityCandidate, candidate_id, organization_id)
    if candidate.status != "draft" or candidate.decision_queue_item_id is not None:
        raise ApiError(
            409, "candidate_not_reviewable", "Only an unqueued draft candidate may enter review."
        )
    queue = DecisionQueueService(session).create(
        DecisionQueueCreate(
            organization_id=organization_id,
            title="Review AI discovered opportunity",
            domain="intelligence",
            reason=(
                f"{candidate.problem_statement}\n"
                f"Confidence: {candidate.confidence_score:.2f}; "
                f"risks: {candidate.risk_summary}"
            ),
            priority="high",
            required_action="review",
        )
    )
    return service.mark_review(candidate, queue.id, actor_id(request))
