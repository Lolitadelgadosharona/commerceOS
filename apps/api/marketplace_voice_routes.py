from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.marketplace_models import (
    CompetitiveMarketplaceObservation,
    MarketplaceEvidenceLink,
    MarketplaceReviewEvidence,
    NormalizedMarketplaceReview,
)
from commerce_os.intelligence.marketplace_schemas import (
    CompetitiveObservationCreate,
    CompetitiveObservationRead,
    MarketplaceEvidenceLinkCreate,
    MarketplaceEvidenceLinkRead,
    MarketplaceReviewCreate,
    MarketplaceReviewRead,
    NormalizedMarketplaceReviewCreate,
    NormalizedMarketplaceReviewRead,
)
from commerce_os.intelligence.marketplace_services import MarketplaceVoiceService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.market_connector_routes import initiating_actor

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/marketplace-review-evidence", response_model=MarketplaceReviewRead, status_code=201)
def capture_review(
    payload: MarketplaceReviewCreate, request: Request, session: SessionDependency
) -> MarketplaceReviewEvidence:
    return MarketplaceVoiceService(session).capture_review(payload, initiating_actor(request))


@router.get("/marketplace-review-evidence", response_model=list[MarketplaceReviewRead])
def list_reviews(
    organization_id: UUID, session: SessionDependency
) -> list[MarketplaceReviewEvidence]:
    return _list(session, MarketplaceReviewEvidence, organization_id)


@router.post(
    "/normalized-marketplace-reviews",
    response_model=NormalizedMarketplaceReviewRead,
    status_code=201,
)
def normalize_review(
    payload: NormalizedMarketplaceReviewCreate, request: Request, session: SessionDependency
) -> NormalizedMarketplaceReview:
    return MarketplaceVoiceService(session).normalize(payload, initiating_actor(request))


@router.get("/normalized-marketplace-reviews", response_model=list[NormalizedMarketplaceReviewRead])
def list_normalized_reviews(
    organization_id: UUID, session: SessionDependency
) -> list[NormalizedMarketplaceReview]:
    return _list(session, NormalizedMarketplaceReview, organization_id)


@router.post(
    "/marketplace-evidence-links", response_model=MarketplaceEvidenceLinkRead, status_code=201
)
def link_evidence(
    payload: MarketplaceEvidenceLinkCreate, request: Request, session: SessionDependency
) -> MarketplaceEvidenceLink:
    return MarketplaceVoiceService(session).link_evidence(payload, initiating_actor(request))


@router.get("/marketplace-evidence-links", response_model=list[MarketplaceEvidenceLinkRead])
def list_evidence_links(
    organization_id: UUID, session: SessionDependency
) -> list[MarketplaceEvidenceLink]:
    return _list(session, MarketplaceEvidenceLink, organization_id)


@router.post(
    "/competitive-marketplace-observations",
    response_model=CompetitiveObservationRead,
    status_code=201,
)
def create_competitive_observation(
    payload: CompetitiveObservationCreate, request: Request, session: SessionDependency
) -> CompetitiveMarketplaceObservation:
    return MarketplaceVoiceService(session).create_competitive_observation(
        payload, initiating_actor(request)
    )


@router.get(
    "/competitive-marketplace-observations", response_model=list[CompetitiveObservationRead]
)
def list_competitive_observations(
    organization_id: UUID, session: SessionDependency
) -> list[CompetitiveMarketplaceObservation]:
    return _list(session, CompetitiveMarketplaceObservation, organization_id)
