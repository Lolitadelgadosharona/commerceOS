from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.creative_intelligence_models import (
    CreativeBriefRecommendation,
    CreativeIntelligenceRun,
    CreativeStrategyRecommendation,
)
from commerce_os.decision.creative_intelligence_schemas import (
    CreativeBriefRecommendationRead,
    CreativeIntelligenceRunCreate,
    CreativeIntelligenceRunRead,
    CreativeStrategyRecommendationRead,
)
from commerce_os.decision.creative_intelligence_services import (
    CreativeIntelligenceService,
    scoped_creative_intelligence,
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


@router.post(
    "/creative-intelligence-runs", response_model=CreativeIntelligenceRunRead, status_code=201
)
def create_run(
    payload: CreativeIntelligenceRunCreate, request: Request, session: SessionDependency
) -> CreativeIntelligenceRun:
    return CreativeIntelligenceService(session).create_run(payload, actor_id(request))


@router.get("/creative-intelligence-runs", response_model=list[CreativeIntelligenceRunRead])
def list_runs(organization_id: UUID, session: SessionDependency) -> list[CreativeIntelligenceRun]:
    return _list(session, CreativeIntelligenceRun, organization_id)


@router.get("/creative-intelligence-runs/{run_id}", response_model=CreativeIntelligenceRunRead)
def get_run(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> CreativeIntelligenceRun:
    return scoped_creative_intelligence(session, CreativeIntelligenceRun, run_id, organization_id)


@router.post(
    "/creative-intelligence-runs/{run_id}/queue", response_model=CreativeIntelligenceRunRead
)
def queue_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> CreativeIntelligenceRun:
    service = CreativeIntelligenceService(session)
    return service.queue(
        scoped_creative_intelligence(session, CreativeIntelligenceRun, run_id, organization_id),
        actor_id(request),
    )


@router.post(
    "/creative-intelligence-runs/{run_id}/cancel", response_model=CreativeIntelligenceRunRead
)
def cancel_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> CreativeIntelligenceRun:
    service = CreativeIntelligenceService(session)
    return service.cancel(
        scoped_creative_intelligence(session, CreativeIntelligenceRun, run_id, organization_id),
        actor_id(request),
    )


@router.get(
    "/creative-strategy-recommendations", response_model=list[CreativeStrategyRecommendationRead]
)
def strategies(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeStrategyRecommendation]:
    return _list(session, CreativeStrategyRecommendation, organization_id)


@router.get("/creative-brief-recommendations", response_model=list[CreativeBriefRecommendationRead])
def briefs(organization_id: UUID, session: SessionDependency) -> list[CreativeBriefRecommendation]:
    return _list(session, CreativeBriefRecommendation, organization_id)
