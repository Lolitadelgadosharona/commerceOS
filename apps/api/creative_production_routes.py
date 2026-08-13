from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.creative_generation_models import CreativeQualityReview
from commerce_os.build.creative_production_models import (
    CreativeProductionAIProvenance,
    CreativeProductionRequest,
    CreativeProductionWork,
)
from commerce_os.build.creative_production_schemas import (
    ArtifactReviewTransition,
    CreativeAIProvenanceCreate,
    CreativeAIProvenanceRead,
    CreativeProductionRequestCreate,
    CreativeProductionRequestRead,
    CreativeProductionRequestTransition,
    CreativeProductionWorkCreate,
    CreativeProductionWorkRead,
    CreativeQualityReviewCreate,
    CreativeQualityReviewRead,
    ProductionArtifactCreate,
    ProductionArtifactRead,
)
from commerce_os.build.creative_production_services import (
    CreativeProductionService,
    scoped_production,
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
    "/creative-production-requests", response_model=CreativeProductionRequestRead, status_code=201
)
def create_request(
    payload: CreativeProductionRequestCreate, request: Request, session: SessionDependency
) -> CreativeProductionRequest:
    return CreativeProductionService(session).create_request(payload, actor_id(request))


@router.get("/creative-production-requests", response_model=list[CreativeProductionRequestRead])
def list_requests(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeProductionRequest]:
    return _list(session, CreativeProductionRequest, organization_id)


@router.patch(
    "/creative-production-requests/{production_request_id}",
    response_model=CreativeProductionRequestRead,
)
def transition_request(
    production_request_id: UUID,
    organization_id: UUID,
    payload: CreativeProductionRequestTransition,
    request: Request,
    session: SessionDependency,
) -> CreativeProductionRequest:
    entity = scoped_production(
        session, CreativeProductionRequest, production_request_id, organization_id
    )
    return CreativeProductionService(session).transition_request(
        entity, payload.status, actor_id(request), payload.approval_request_id
    )


@router.post(
    "/creative-production-work", response_model=CreativeProductionWorkRead, status_code=201
)
def create_work(
    payload: CreativeProductionWorkCreate, request: Request, session: SessionDependency
) -> CreativeProductionWork:
    return CreativeProductionService(session).create_work(payload, actor_id(request))


@router.get("/creative-production-work", response_model=list[CreativeProductionWorkRead])
def list_work(organization_id: UUID, session: SessionDependency) -> list[CreativeProductionWork]:
    return _list(session, CreativeProductionWork, organization_id)


@router.post(
    "/creative-production-ai-provenance", response_model=CreativeAIProvenanceRead, status_code=201
)
def link_ai(
    payload: CreativeAIProvenanceCreate, request: Request, session: SessionDependency
) -> CreativeProductionAIProvenance:
    return CreativeProductionService(session).link_ai_provenance(payload, actor_id(request))


@router.get("/creative-production-ai-provenance", response_model=list[CreativeAIProvenanceRead])
def list_ai(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeProductionAIProvenance]:
    return _list(session, CreativeProductionAIProvenance, organization_id)


@router.post(
    "/creative-production-artifacts", response_model=ProductionArtifactRead, status_code=201
)
def create_artifact(
    payload: ProductionArtifactCreate, request: Request, session: SessionDependency
) -> CreativeAsset:
    return CreativeProductionService(session).create_artifact(payload, actor_id(request))


@router.get("/creative-production-artifacts", response_model=list[ProductionArtifactRead])
def list_artifacts(organization_id: UUID, session: SessionDependency) -> list[CreativeAsset]:
    return _list(session, CreativeAsset, organization_id)


@router.patch("/creative-production-artifacts/{asset_id}", response_model=ProductionArtifactRead)
def transition_artifact(
    asset_id: UUID,
    organization_id: UUID,
    payload: ArtifactReviewTransition,
    request: Request,
    session: SessionDependency,
) -> CreativeAsset:
    asset = scoped_production(session, CreativeAsset, asset_id, organization_id)
    return CreativeProductionService(session).transition_artifact(
        asset, payload.review_status, actor_id(request)
    )


@router.post(
    "/creative-production-quality-reviews",
    response_model=CreativeQualityReviewRead,
    status_code=201,
)
def create_quality_review(
    payload: CreativeQualityReviewCreate, request: Request, session: SessionDependency
) -> CreativeQualityReview:
    return CreativeProductionService(session).review_quality(payload, actor_id(request))


@router.get("/creative-production-quality-reviews", response_model=list[CreativeQualityReviewRead])
def list_quality_reviews(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeQualityReview]:
    return _list(session, CreativeQualityReview, organization_id)
