from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.listing_geo_intelligence_models import (
    FAQRecommendation,
    GEOContentRecommendation,
    ListingIntelligenceRun,
    ListingStrategyRecommendation,
)
from commerce_os.decision.listing_geo_intelligence_schemas import (
    FAQRecommendationRead,
    GEOContentRecommendationRead,
    ListingIntelligenceRunCreate,
    ListingIntelligenceRunRead,
    ListingStrategyRecommendationRead,
)
from commerce_os.decision.listing_geo_intelligence_services import (
    ListingIntelligenceService,
    scoped_listing_intelligence,
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
    "/listing-intelligence-runs", response_model=ListingIntelligenceRunRead, status_code=201
)
def create_run(
    payload: ListingIntelligenceRunCreate, request: Request, session: SessionDependency
) -> ListingIntelligenceRun:
    return ListingIntelligenceService(session).create_run(payload, actor_id(request))


@router.get("/listing-intelligence-runs", response_model=list[ListingIntelligenceRunRead])
def list_runs(organization_id: UUID, session: SessionDependency) -> list[ListingIntelligenceRun]:
    return _list(session, ListingIntelligenceRun, organization_id)


@router.get("/listing-intelligence-runs/{run_id}", response_model=ListingIntelligenceRunRead)
def get_run(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> ListingIntelligenceRun:
    return scoped_listing_intelligence(session, ListingIntelligenceRun, run_id, organization_id)


@router.post("/listing-intelligence-runs/{run_id}/queue", response_model=ListingIntelligenceRunRead)
def queue_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ListingIntelligenceRun:
    service = ListingIntelligenceService(session)
    return service.queue(
        scoped_listing_intelligence(session, ListingIntelligenceRun, run_id, organization_id),
        actor_id(request),
    )


@router.post(
    "/listing-intelligence-runs/{run_id}/cancel", response_model=ListingIntelligenceRunRead
)
def cancel_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ListingIntelligenceRun:
    service = ListingIntelligenceService(session)
    return service.cancel(
        scoped_listing_intelligence(session, ListingIntelligenceRun, run_id, organization_id),
        actor_id(request),
    )


@router.get(
    "/listing-strategy-recommendations", response_model=list[ListingStrategyRecommendationRead]
)
def listing_recommendations(
    organization_id: UUID, session: SessionDependency
) -> list[ListingStrategyRecommendation]:
    return _list(session, ListingStrategyRecommendation, organization_id)


@router.get("/geo-content-recommendations", response_model=list[GEOContentRecommendationRead])
def geo_recommendations(
    organization_id: UUID, session: SessionDependency
) -> list[GEOContentRecommendation]:
    return _list(session, GEOContentRecommendation, organization_id)


@router.get("/faq-recommendations", response_model=list[FAQRecommendationRead])
def faq_recommendations(
    organization_id: UUID, session: SessionDependency
) -> list[FAQRecommendation]:
    return _list(session, FAQRecommendation, organization_id)
