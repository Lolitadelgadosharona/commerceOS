from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.decision.cfo_models import CFOInsight
from commerce_os.decision.cfo_schemas import CFOInsightCreate, CFOInsightRead
from commerce_os.decision.cfo_services import CFOInsightService
from commerce_os.finance.models import (
    ContributionProfitAssessment,
    CostObservation,
    FinancialPeriod,
    FinancialRiskSignal,
    RevenueObservation,
    UnitEconomicAssessment,
)
from commerce_os.finance.schemas import (
    ContributionProfitCreate,
    ContributionProfitRead,
    CostObservationCreate,
    CostObservationRead,
    FinancialPeriodCreate,
    FinancialPeriodRead,
    FinancialPeriodUpdate,
    FinancialRiskCreate,
    FinancialRiskRead,
    RevenueObservationCreate,
    RevenueObservationRead,
    UnitEconomicsCreate,
    UnitEconomicsRead,
)
from commerce_os.finance.services import FinanceIntelligenceService, scoped_period
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


@router.post("/financial-periods", response_model=FinancialPeriodRead, status_code=201)
def create_period(payload: FinancialPeriodCreate, session: SessionDependency) -> FinancialPeriod:
    return FinanceIntelligenceService(session).create_period(payload)


@router.get("/financial-periods", response_model=list[FinancialPeriodRead])
def list_periods(organization_id: UUID, session: SessionDependency) -> list[FinancialPeriod]:
    return _list(session, FinancialPeriod, organization_id)


@router.patch("/financial-periods/{period_id}", response_model=FinancialPeriodRead)
def transition_period(
    period_id: UUID,
    organization_id: UUID,
    payload: FinancialPeriodUpdate,
    session: SessionDependency,
) -> FinancialPeriod:
    return FinanceIntelligenceService(session).transition_period(
        scoped_period(session, period_id, organization_id), payload.status
    )


@router.post("/revenue-observations", response_model=RevenueObservationRead, status_code=201)
def create_revenue(
    payload: RevenueObservationCreate, session: SessionDependency
) -> RevenueObservation:
    return FinanceIntelligenceService(session).create_revenue(payload)


@router.get("/revenue-observations", response_model=list[RevenueObservationRead])
def list_revenue(organization_id: UUID, session: SessionDependency) -> list[RevenueObservation]:
    return _list(session, RevenueObservation, organization_id)


@router.post("/cost-observations", response_model=CostObservationRead, status_code=201)
def create_cost(payload: CostObservationCreate, session: SessionDependency) -> CostObservation:
    return FinanceIntelligenceService(session).create_cost(payload)


@router.get("/cost-observations", response_model=list[CostObservationRead])
def list_costs(organization_id: UUID, session: SessionDependency) -> list[CostObservation]:
    return _list(session, CostObservation, organization_id)


@router.post("/contribution-profit", response_model=ContributionProfitRead, status_code=201)
def assess_contribution(
    payload: ContributionProfitCreate, session: SessionDependency
) -> ContributionProfitAssessment:
    return FinanceIntelligenceService(session).assess_contribution(payload)


@router.get("/contribution-profit", response_model=list[ContributionProfitRead])
def list_contribution(
    organization_id: UUID, session: SessionDependency
) -> list[ContributionProfitAssessment]:
    return _list(session, ContributionProfitAssessment, organization_id)


@router.post("/unit-economics", response_model=UnitEconomicsRead, status_code=201)
def assess_unit_economics(
    payload: UnitEconomicsCreate, session: SessionDependency
) -> UnitEconomicAssessment:
    return FinanceIntelligenceService(session).assess_unit_economics(payload)


@router.get("/unit-economics", response_model=list[UnitEconomicsRead])
def list_unit_economics(
    organization_id: UUID, session: SessionDependency
) -> list[UnitEconomicAssessment]:
    return _list(session, UnitEconomicAssessment, organization_id)


@router.post("/cfo-insights", response_model=CFOInsightRead, status_code=201)
def create_cfo_insight(payload: CFOInsightCreate, session: SessionDependency) -> CFOInsight:
    return CFOInsightService(session).create(payload)


@router.get("/cfo-insights", response_model=list[CFOInsightRead])
def list_cfo_insights(organization_id: UUID, session: SessionDependency) -> list[CFOInsight]:
    return _list(session, CFOInsight, organization_id)


@router.post("/financial-risk-signals", response_model=FinancialRiskRead, status_code=201)
def create_financial_risk(
    payload: FinancialRiskCreate, session: SessionDependency
) -> FinancialRiskSignal:
    return FinanceIntelligenceService(session).create_risk(payload)


@router.get("/financial-risk-signals", response_model=list[FinancialRiskRead])
def list_financial_risks(
    organization_id: UUID, session: SessionDependency
) -> list[FinancialRiskSignal]:
    return _list(session, FinancialRiskSignal, organization_id)
