from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.commercial_risk_models import ProductRiskAssessment
from commerce_os.intelligence.economics_models import (
    ProductEconomicProfile,
    ProductProfitAssessment,
    ProfitRecommendation,
    ProfitScenario,
    ProfitScenarioAssessment,
    RiskAdjustedProfitAssessment,
)
from commerce_os.intelligence.economics_schemas import (
    ProductEconomicProfileCreate,
    ProductProfitAssessmentCreate,
    ProfitScenarioCreate,
    RiskAdjustedProfitCreate,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import ProductCandidate
from commerce_os.shared.database import Base

MONEY = Decimal("0.0001")
SCORE = Decimal("0.0001")
HUNDRED = Decimal(100)
FORMULA_VERSION = "product-profit-v1"
SCENARIO_FACTORS = {
    ProfitScenario.CONSERVATIVE: (Decimal("0.90"), Decimal("1.10"), Decimal("1.25")),
    ProfitScenario.BASE: (Decimal("1.00"), Decimal("1.00"), Decimal("1.00")),
    ProfitScenario.OPTIMISTIC: (Decimal("1.05"), Decimal("0.95"), Decimal("0.75")),
}
EntityT = TypeVar("EntityT", bound=Base)


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE, rounding=ROUND_HALF_UP)


class ProductEconomicsIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_profile(self, payload: ProductEconomicProfileCreate) -> ProductEconomicProfile:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        values = payload.model_dump()
        for field in (
            "product_cost",
            "shipping_cost",
            "packaging_cost",
            "transaction_cost",
            "estimated_acquisition_cost",
        ):
            values[field] = quantize_money(values[field])
        return self._save(ProductEconomicProfile(**values))

    def assess_profit(self, payload: ProductProfitAssessmentCreate) -> ProductProfitAssessment:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        profile = self._latest_profile(payload.product_candidate_id, payload.organization_id)
        price = quantize_money(payload.selling_price)
        gross_margin = quantize_money(
            price
            - profile.product_cost
            - profile.shipping_cost
            - profile.packaging_cost
            - profile.transaction_cost
        )
        refund_impact = price * profile.refund_rate_assumption
        dispute_impact = price * profile.dispute_rate_assumption
        contribution = quantize_money(
            gross_margin - profile.estimated_acquisition_cost - refund_impact - dispute_impact
        )
        margin_score = quantize_score(max(Decimal(0), min(HUNDRED, contribution / price * HUNDRED)))
        return self._save(
            ProductProfitAssessment(
                organization_id=payload.organization_id,
                product_candidate_id=payload.product_candidate_id,
                selling_price=price,
                gross_margin=gross_margin,
                contribution_profit=contribution,
                margin_score=margin_score,
                confidence=profile.confidence,
                formula_version=FORMULA_VERSION,
            )
        )

    def assess_scenario(self, payload: ProfitScenarioCreate) -> ProfitScenarioAssessment:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        profile = self._latest_profile(payload.product_candidate_id, payload.organization_id)
        profit = self._latest_profit(payload.product_candidate_id, payload.organization_id)
        revenue_factor, cost_factor, rate_factor = SCENARIO_FACTORS[payload.scenario]
        revenue = quantize_money(profit.selling_price * revenue_factor)
        operating_cost = (
            profile.product_cost
            + profile.shipping_cost
            + profile.packaging_cost
            + profile.transaction_cost
            + profile.estimated_acquisition_cost
        ) * cost_factor
        refund_rate = min(Decimal(1), profile.refund_rate_assumption * rate_factor)
        dispute_rate = min(Decimal(1), profile.dispute_rate_assumption * rate_factor)
        cost = quantize_money(operating_cost + revenue * refund_rate + revenue * dispute_rate)
        scenario_profit = quantize_money(revenue - cost)
        margin = quantize_score(scenario_profit / revenue * HUNDRED)
        return self._save(
            ProfitScenarioAssessment(
                organization_id=payload.organization_id,
                product_candidate_id=payload.product_candidate_id,
                scenario=payload.scenario,
                revenue=revenue,
                cost=cost,
                profit=scenario_profit,
                margin=margin,
            )
        )

    def assess_risk_adjusted(
        self, payload: RiskAdjustedProfitCreate
    ) -> RiskAdjustedProfitAssessment:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        profit = self._latest_profit(payload.product_candidate_id, payload.organization_id)
        risk = self.session.scalar(
            select(ProductRiskAssessment)
            .where(
                ProductRiskAssessment.organization_id == payload.organization_id,
                ProductRiskAssessment.product_candidate_id == payload.product_candidate_id,
            )
            .order_by(ProductRiskAssessment.created_at.desc(), ProductRiskAssessment.id.desc())
        )
        if risk is None:
            raise IntelligenceValidationError(
                "Risk-adjusted profit requires a product risk assessment."
            )
        opportunity_score = quantize_score(payload.opportunity_score)
        risk_score = quantize_score(Decimal(str(risk.risk_score)))
        profit_score = quantize_score(profit.margin_score)
        final_score = quantize_score(
            opportunity_score * Decimal("0.35")
            + (HUNDRED - risk_score) * Decimal("0.35")
            + profit_score * Decimal("0.30")
        )
        recommendation = self.recommendation(final_score, risk_score)
        return self._save(
            RiskAdjustedProfitAssessment(
                organization_id=payload.organization_id,
                product_candidate_id=payload.product_candidate_id,
                opportunity_score=opportunity_score,
                risk_score=risk_score,
                profit_score=profit_score,
                final_score=final_score,
                recommendation=recommendation,
            )
        )

    @staticmethod
    def recommendation(final_score: Decimal, risk_score: Decimal) -> ProfitRecommendation:
        if risk_score >= 75 or final_score < 40:
            return ProfitRecommendation.REJECT
        if final_score >= 70 and risk_score < 40:
            return ProfitRecommendation.GO
        if final_score >= 55 and risk_score < 60:
            return ProfitRecommendation.TEST
        return ProfitRecommendation.REVIEW

    def _candidate(self, candidate_id: UUID, organization_id: UUID) -> ProductCandidate:
        candidate = self.session.get(ProductCandidate, candidate_id)
        if candidate is None or candidate.organization_id != organization_id:
            raise IntelligenceScopeError("Product candidate was not found in this organization.")
        return candidate

    def _latest_profile(self, candidate_id: UUID, organization_id: UUID) -> ProductEconomicProfile:
        profile = self.session.scalar(
            select(ProductEconomicProfile)
            .where(
                ProductEconomicProfile.organization_id == organization_id,
                ProductEconomicProfile.product_candidate_id == candidate_id,
            )
            .order_by(ProductEconomicProfile.created_at.desc(), ProductEconomicProfile.id.desc())
        )
        if profile is None:
            raise IntelligenceValidationError("Profit assessment requires an economic profile.")
        return profile

    def _latest_profit(self, candidate_id: UUID, organization_id: UUID) -> ProductProfitAssessment:
        profit = self.session.scalar(
            select(ProductProfitAssessment)
            .where(
                ProductProfitAssessment.organization_id == organization_id,
                ProductProfitAssessment.product_candidate_id == candidate_id,
            )
            .order_by(ProductProfitAssessment.created_at.desc(), ProductProfitAssessment.id.desc())
        )
        if profit is None:
            raise IntelligenceValidationError("Scenario requires a product profit assessment.")
        return profit

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
