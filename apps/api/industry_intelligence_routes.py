from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.industry_intelligence_models import (
    GrowthGEOAssessment,
    GrowthServiceRecommendation,
    IndustryGrowthEvidence,
    IndustryGrowthPattern,
    IndustryGrowthProfile,
    IndustryLearningSignal,
)
from commerce_os.growth.industry_intelligence_schemas import (
    GEOAssessmentCreate,
    GEOAssessmentRead,
    IndustryEvidenceCreate,
    IndustryEvidenceRead,
    IndustryLearningSignalCreate,
    IndustryLearningSignalRead,
    IndustryPatternCreate,
    IndustryPatternRead,
    IndustryProfileCreate,
    IndustryProfileRead,
    ServiceRecommendationCreate,
    ServiceRecommendationRead,
)
from commerce_os.growth.industry_intelligence_services import IndustryIntelligenceService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.growth_revenue_routes import actor_id

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


@router.post("/industry-growth-profiles", response_model=IndustryProfileRead, status_code=201)
def create_profile(
    payload: IndustryProfileCreate, request: Request, session: SessionDependency
) -> IndustryGrowthProfile:
    return IndustryIntelligenceService(session).create_profile(payload, actor_id(request))


@router.get("/industry-growth-profiles", response_model=list[IndustryProfileRead])
def list_profiles(organization_id: UUID, session: SessionDependency) -> list[IndustryGrowthProfile]:
    return _list(session, IndustryGrowthProfile, organization_id)


@router.post("/industry-growth-evidence", response_model=IndustryEvidenceRead, status_code=201)
def create_evidence(
    payload: IndustryEvidenceCreate, request: Request, session: SessionDependency
) -> IndustryGrowthEvidence:
    return IndustryIntelligenceService(session).create_evidence(payload, actor_id(request))


@router.get("/industry-growth-evidence", response_model=list[IndustryEvidenceRead])
def list_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[IndustryGrowthEvidence]:
    return _list(session, IndustryGrowthEvidence, organization_id)


@router.post("/industry-growth-patterns", response_model=IndustryPatternRead, status_code=201)
def create_pattern(
    payload: IndustryPatternCreate, request: Request, session: SessionDependency
) -> IndustryGrowthPattern:
    return IndustryIntelligenceService(session).create_pattern(payload, actor_id(request))


@router.get("/industry-growth-patterns", response_model=list[IndustryPatternRead])
def list_patterns(organization_id: UUID, session: SessionDependency) -> list[IndustryGrowthPattern]:
    return _list(session, IndustryGrowthPattern, organization_id)


@router.post("/growth-geo-assessments", response_model=GEOAssessmentRead, status_code=201)
def create_geo(
    payload: GEOAssessmentCreate, request: Request, session: SessionDependency
) -> GrowthGEOAssessment:
    return IndustryIntelligenceService(session).create_geo_assessment(payload, actor_id(request))


@router.get("/growth-geo-assessments", response_model=list[GEOAssessmentRead])
def list_geo(organization_id: UUID, session: SessionDependency) -> list[GrowthGEOAssessment]:
    return _list(session, GrowthGEOAssessment, organization_id)


@router.post(
    "/growth-service-recommendations", response_model=ServiceRecommendationRead, status_code=201
)
def create_service(
    payload: ServiceRecommendationCreate, request: Request, session: SessionDependency
) -> GrowthServiceRecommendation:
    return IndustryIntelligenceService(session).create_service_recommendation(
        payload, actor_id(request)
    )


@router.get("/growth-service-recommendations", response_model=list[ServiceRecommendationRead])
def list_services(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthServiceRecommendation]:
    return _list(session, GrowthServiceRecommendation, organization_id)


@router.post(
    "/industry-learning-signals", response_model=IndustryLearningSignalRead, status_code=201
)
def create_learning(
    payload: IndustryLearningSignalCreate, request: Request, session: SessionDependency
) -> IndustryLearningSignal:
    return IndustryIntelligenceService(session).create_learning_signal(payload, actor_id(request))


@router.get("/industry-learning-signals", response_model=list[IndustryLearningSignalRead])
def list_learning(
    organization_id: UUID, session: SessionDependency
) -> list[IndustryLearningSignal]:
    return _list(session, IndustryLearningSignal, organization_id)
