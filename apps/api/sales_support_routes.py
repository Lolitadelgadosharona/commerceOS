from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.decision.sales_support_models import (
    CustomerRiskSignal,
    RecommendationStatus,
    SalesIntelligenceProfile,
    SalesRecommendation,
    SupportCaseIntelligence,
)
from commerce_os.decision.sales_support_schemas import (
    RecommendationCreate,
    RecommendationRead,
    RecommendationUpdate,
    RiskSignalCreate,
    RiskSignalRead,
    SalesProfileCreate,
    SalesProfileRead,
    SupportIntelligenceCreate,
    SupportIntelligenceRead,
)
from commerce_os.decision.sales_support_services import (
    SalesSupportDecisionService,
    scoped_recommendation,
)
from commerce_os.governance.errors import NotFoundError
from commerce_os.governance.models import AIActionPolicy, Organization
from commerce_os.governance.schemas import AIActionPolicyCreate, AIActionPolicyRead
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post("/sales-intelligence", response_model=SalesProfileRead, status_code=201)
def create_sales_profile(
    payload: SalesProfileCreate, session: SessionDependency
) -> SalesIntelligenceProfile:
    return SalesSupportDecisionService(session).create_profile(payload)


@router.get("/sales-intelligence", response_model=list[SalesProfileRead])
def list_sales_profiles(
    organization_id: UUID, session: SessionDependency
) -> list[SalesIntelligenceProfile]:
    return _list(session, SalesIntelligenceProfile, organization_id)


@router.post("/sales-recommendations", response_model=RecommendationRead, status_code=201)
def create_recommendation(
    payload: RecommendationCreate, session: SessionDependency
) -> SalesRecommendation:
    return SalesSupportDecisionService(session).create_recommendation(payload)


@router.get("/sales-recommendations", response_model=list[RecommendationRead])
def list_recommendations(
    organization_id: UUID, session: SessionDependency
) -> list[SalesRecommendation]:
    return _list(session, SalesRecommendation, organization_id)


@router.patch("/sales-recommendations/{recommendation_id}", response_model=RecommendationRead)
def transition_recommendation(
    recommendation_id: UUID,
    organization_id: UUID,
    payload: RecommendationUpdate,
    session: SessionDependency,
) -> SalesRecommendation:
    return SalesSupportDecisionService(session).transition_recommendation(
        scoped_recommendation(session, recommendation_id, organization_id),
        RecommendationStatus(payload.status),
    )


@router.post("/support-intelligence", response_model=SupportIntelligenceRead, status_code=201)
def create_support(
    payload: SupportIntelligenceCreate, session: SessionDependency
) -> SupportCaseIntelligence:
    return SalesSupportDecisionService(session).create_support(payload)


@router.get("/support-intelligence", response_model=list[SupportIntelligenceRead])
def list_support(
    organization_id: UUID, session: SessionDependency
) -> list[SupportCaseIntelligence]:
    return _list(session, SupportCaseIntelligence, organization_id)


@router.post("/customer-risk-signals", response_model=RiskSignalRead, status_code=201)
def create_risk(payload: RiskSignalCreate, session: SessionDependency) -> CustomerRiskSignal:
    return SalesSupportDecisionService(session).create_risk(payload)


@router.get("/customer-risk-signals", response_model=list[RiskSignalRead])
def list_risks(organization_id: UUID, session: SessionDependency) -> list[CustomerRiskSignal]:
    return _list(session, CustomerRiskSignal, organization_id)


@router.post("/ai-action-policies", response_model=AIActionPolicyRead, status_code=201)
def create_ai_policy(payload: AIActionPolicyCreate, session: SessionDependency) -> AIActionPolicy:
    if session.get(Organization, payload.organization_id) is None:
        raise NotFoundError("Organization was not found.")
    policy = AIActionPolicy(**payload.model_dump())
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.get("/ai-action-policies", response_model=list[AIActionPolicyRead])
def list_ai_policies(organization_id: UUID, session: SessionDependency) -> list[AIActionPolicy]:
    return _list(session, AIActionPolicy, organization_id)
