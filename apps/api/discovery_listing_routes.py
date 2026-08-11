from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.discovery_listing_models import (
    AIDiscoveryReadinessAssessment,
    GeoKnowledgeAsset,
    ListingBlueprint,
    ListingQualityAssessment,
)
from commerce_os.decision.discovery_listing_schemas import (
    AIDiscoveryReadinessRead,
    GeoKnowledgeAssetCreate,
    GeoKnowledgeAssetRead,
    ListingAssessmentCreate,
    ListingBlueprintCreate,
    ListingBlueprintRead,
    ListingQualityRead,
)
from commerce_os.decision.discovery_listing_services import DiscoveryListingService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

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


@router.post("/listing-blueprints", response_model=ListingBlueprintRead, status_code=201)
def create_blueprint(
    payload: ListingBlueprintCreate, session: SessionDependency
) -> ListingBlueprint:
    return DiscoveryListingService(session).create_blueprint(payload)


@router.get("/listing-blueprints", response_model=list[ListingBlueprintRead])
def list_blueprints(organization_id: UUID, session: SessionDependency) -> list[ListingBlueprint]:
    return _list(session, ListingBlueprint, organization_id)


@router.post("/geo-assets", response_model=GeoKnowledgeAssetRead, status_code=201)
def create_geo_asset(
    payload: GeoKnowledgeAssetCreate, session: SessionDependency
) -> GeoKnowledgeAsset:
    return DiscoveryListingService(session).create_geo_asset(payload)


@router.get("/geo-assets", response_model=list[GeoKnowledgeAssetRead])
def list_geo_assets(organization_id: UUID, session: SessionDependency) -> list[GeoKnowledgeAsset]:
    return _list(session, GeoKnowledgeAsset, organization_id)


@router.post("/listing-quality-assessments", response_model=ListingQualityRead, status_code=201)
def create_quality_assessment(
    payload: ListingAssessmentCreate, session: SessionDependency
) -> ListingQualityAssessment:
    return DiscoveryListingService(session).assess_quality(payload)


@router.get("/listing-quality-assessments", response_model=list[ListingQualityRead])
def list_quality_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[ListingQualityAssessment]:
    return _list(session, ListingQualityAssessment, organization_id)


@router.post("/ai-discovery-readiness", response_model=AIDiscoveryReadinessRead, status_code=201)
def create_discovery_readiness(
    payload: ListingAssessmentCreate, session: SessionDependency
) -> AIDiscoveryReadinessAssessment:
    return DiscoveryListingService(session).assess_discovery(payload)


@router.get("/ai-discovery-readiness", response_model=list[AIDiscoveryReadinessRead])
def list_discovery_readiness(
    organization_id: UUID, session: SessionDependency
) -> list[AIDiscoveryReadinessAssessment]:
    return _list(session, AIDiscoveryReadinessAssessment, organization_id)
