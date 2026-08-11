from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.economics_models import (
    ProductEconomicProfile,
    ProductProfitAssessment,
    ProfitScenarioAssessment,
    RiskAdjustedProfitAssessment,
)
from commerce_os.intelligence.economics_schemas import (
    ProductEconomicProfileCreate,
    ProductEconomicProfileRead,
    ProductProfitAssessmentCreate,
    ProductProfitAssessmentRead,
    ProfitScenarioCreate,
    ProfitScenarioRead,
    RiskAdjustedProfitCreate,
    RiskAdjustedProfitRead,
)
from commerce_os.intelligence.economics_services import ProductEconomicsIntelligenceService
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


@router.post(
    "/product-economic-profiles", response_model=ProductEconomicProfileRead, status_code=201
)
def create_profile(
    payload: ProductEconomicProfileCreate, session: SessionDependency
) -> ProductEconomicProfile:
    return ProductEconomicsIntelligenceService(session).create_profile(payload)


@router.get("/product-economic-profiles", response_model=list[ProductEconomicProfileRead])
def list_profiles(
    organization_id: UUID, session: SessionDependency
) -> list[ProductEconomicProfile]:
    return _list(session, ProductEconomicProfile, organization_id)


@router.post(
    "/product-profit-assessments", response_model=ProductProfitAssessmentRead, status_code=201
)
def create_profit_assessment(
    payload: ProductProfitAssessmentCreate, session: SessionDependency
) -> ProductProfitAssessment:
    return ProductEconomicsIntelligenceService(session).assess_profit(payload)


@router.get("/product-profit-assessments", response_model=list[ProductProfitAssessmentRead])
def list_profit_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[ProductProfitAssessment]:
    return _list(session, ProductProfitAssessment, organization_id)


@router.post("/profit-scenarios", response_model=ProfitScenarioRead, status_code=201)
def create_scenario(
    payload: ProfitScenarioCreate, session: SessionDependency
) -> ProfitScenarioAssessment:
    return ProductEconomicsIntelligenceService(session).assess_scenario(payload)


@router.get("/profit-scenarios", response_model=list[ProfitScenarioRead])
def list_scenarios(
    organization_id: UUID, session: SessionDependency
) -> list[ProfitScenarioAssessment]:
    return _list(session, ProfitScenarioAssessment, organization_id)


@router.post(
    "/risk-adjusted-profit-assessments",
    response_model=RiskAdjustedProfitRead,
    status_code=201,
)
def create_risk_adjusted(
    payload: RiskAdjustedProfitCreate, session: SessionDependency
) -> RiskAdjustedProfitAssessment:
    return ProductEconomicsIntelligenceService(session).assess_risk_adjusted(payload)


@router.get("/risk-adjusted-profit-assessments", response_model=list[RiskAdjustedProfitRead])
def list_risk_adjusted(
    organization_id: UUID, session: SessionDependency
) -> list[RiskAdjustedProfitAssessment]:
    return _list(session, RiskAdjustedProfitAssessment, organization_id)
