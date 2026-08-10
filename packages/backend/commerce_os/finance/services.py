from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.finance.errors import FinanceError
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
    CostObservationCreate,
    FinancialPeriodCreate,
    FinancialRiskCreate,
    RevenueObservationCreate,
    UnitEconomicsCreate,
)
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
CONTRIBUTION_CATEGORIES = (
    "product_cost",
    "shipping_cost",
    "ad_cost",
    "refund_cost",
    "dispute_cost",
    "operation_cost",
)
PERIOD_TRANSITIONS = {"open": {"closed"}, "closed": {"locked"}, "locked": set()}


def scoped_period(session: Session, entity_id: UUID, organization_id: UUID) -> FinancialPeriod:
    period = session.get(FinancialPeriod, entity_id)
    if period is None or period.organization_id != organization_id:
        raise FinanceError("Financial period was not found in this organization.", "not_found")
    return period


class FinanceIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_period(self, payload: FinancialPeriodCreate) -> FinancialPeriod:
        if not self._organization_exists(payload.organization_id):
            raise FinanceError("Organization was not found.", "not_found")
        return self._save(FinancialPeriod(**payload.model_dump(), status="open"))

    def transition_period(self, period: FinancialPeriod, status: str) -> FinancialPeriod:
        if status not in PERIOD_TRANSITIONS[period.status]:
            raise FinanceError(f"Period cannot transition from {period.status} to {status}.")
        period.status = status
        return self._save(period)

    def create_revenue(self, payload: RevenueObservationCreate) -> RevenueObservation:
        self._validate_reference("projects", payload.project_id, payload.organization_id, "Project")
        if payload.product_id:
            self._validate_reference(
                "products", payload.product_id, payload.organization_id, "Product"
            )
        return self._save(RevenueObservation(**payload.model_dump()))

    def create_cost(self, payload: CostObservationCreate) -> CostObservation:
        self._validate_reference("products", payload.product_id, payload.organization_id, "Product")
        return self._save(CostObservation(**payload.model_dump()))

    def assess_contribution(
        self, payload: ContributionProfitCreate
    ) -> ContributionProfitAssessment:
        self._validate_reference("products", payload.product_id, payload.organization_id, "Product")
        period = scoped_period(self.session, payload.period_id, payload.organization_id)
        revenue = self.session.scalar(
            select(func.coalesce(func.sum(RevenueObservation.amount), 0)).where(
                RevenueObservation.organization_id == payload.organization_id,
                RevenueObservation.product_id == payload.product_id,
                RevenueObservation.currency == payload.currency,
                RevenueObservation.observation_date.between(period.start_date, period.end_date),
            )
        )
        rows = self.session.execute(
            select(CostObservation.category, func.sum(CostObservation.amount))
            .where(
                CostObservation.organization_id == payload.organization_id,
                CostObservation.product_id == payload.product_id,
                CostObservation.currency == payload.currency,
                CostObservation.category.in_(CONTRIBUTION_CATEGORIES),
                CostObservation.observation_date.between(period.start_date, period.end_date),
            )
            .group_by(CostObservation.category)
        ).all()
        components = {category: Decimal(amount) for category, amount in rows}
        for category in CONTRIBUTION_CATEGORIES:
            components.setdefault(category, Decimal("0"))
        revenue_value = Decimal(revenue or 0)
        total_cost = sum(components.values(), Decimal("0"))
        profit = revenue_value - total_cost
        margin = round(float(profit / revenue_value * 100), 2) if revenue_value else 0.0
        return self._save(
            ContributionProfitAssessment(
                organization_id=payload.organization_id,
                product_id=payload.product_id,
                period_id=payload.period_id,
                currency=payload.currency,
                revenue=revenue_value,
                cost=total_cost,
                contribution_profit=profit,
                margin_percentage=margin,
                confidence=payload.confidence,
                component_snapshot={key: str(value) for key, value in components.items()},
                formula_version="contribution-profit-v1.0",
            )
        )

    def assess_unit_economics(self, payload: UnitEconomicsCreate) -> UnitEconomicAssessment:
        self._validate_reference("products", payload.product_id, payload.organization_id, "Product")
        ltv = float(payload.lifetime_value_estimate)
        cac = float(payload.customer_acquisition_cost)
        efficiency = max(-1.0, min(1.0, (ltv - cac) / max(ltv, 1.0)))
        net_margin = payload.gross_margin - payload.refund_rate - payload.dispute_rate
        score = round(max(0.0, min(100.0, 50 + 25 * (net_margin + efficiency))), 2)
        return self._save(
            UnitEconomicAssessment(
                **payload.model_dump(),
                profitability_score=score,
                formula_version="unit-economics-v1.0",
            )
        )

    def create_risk(self, payload: FinancialRiskCreate) -> FinancialRiskSignal:
        if payload.period_id:
            scoped_period(self.session, payload.period_id, payload.organization_id)
        if payload.product_id:
            self._validate_reference(
                "products", payload.product_id, payload.organization_id, "Product"
            )
        if not payload.period_id and not payload.product_id:
            raise FinanceError("Financial risk requires period or product evidence scope.")
        return self._save(FinancialRiskSignal(**payload.model_dump()))

    def _organization_exists(self, organization_id: UUID) -> bool:
        table = Base.metadata.tables["organizations"]
        return (
            self.session.execute(
                select(table.c.id).where(table.c.id == organization_id)
            ).scalar_one_or_none()
            is not None
        )

    def _validate_reference(
        self, table: str, reference_id: UUID, organization_id: UUID, label: str
    ) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name=table,
            reference_id=reference_id,
            organization_id=organization_id,
        ):
            raise FinanceError(f"{label} was not found in this organization.", "not_found")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
