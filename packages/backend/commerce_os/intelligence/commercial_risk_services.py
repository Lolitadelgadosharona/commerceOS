from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.commercial_risk_models import (
    CommercialRecommendation,
    CommercialViabilityAssessment,
    ProductRiskAssessment,
    ProductRiskSignal,
    ProductRiskStatus,
)
from commerce_os.intelligence.commercial_risk_schemas import (
    CommercialViabilityCreate,
    ProductRiskAssessmentCreate,
    ProductRiskSignalCreate,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import ProductCandidate
from commerce_os.shared.database import Base

SEVERITY_WEIGHT = {"low": 25.0, "medium": 50.0, "high": 75.0, "critical": 100.0}
SIGNAL_TRANSITIONS = {
    ProductRiskStatus.OPEN: {
        ProductRiskStatus.MITIGATED,
        ProductRiskStatus.ACCEPTED,
        ProductRiskStatus.DISMISSED,
    }
}
EntityT = TypeVar("EntityT", bound=Base)


class CommercialRiskService:
    formula_version = "product-commercial-risk-v1"

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_signal(self, payload: ProductRiskSignalCreate) -> ProductRiskSignal:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        return self._save(ProductRiskSignal(**payload.model_dump(), status=ProductRiskStatus.OPEN))

    def transition_signal(self, signal: ProductRiskSignal, status: str) -> ProductRiskSignal:
        next_status = ProductRiskStatus(status)
        if next_status not in SIGNAL_TRANSITIONS.get(signal.status, set()):
            raise IntelligenceValidationError(
                f"Product risk signal cannot transition from {signal.status} to {status}."
            )
        signal.status = next_status
        return self._save(signal)

    def assess_risk(self, payload: ProductRiskAssessmentCreate) -> ProductRiskAssessment:
        self._candidate(payload.product_candidate_id, payload.organization_id)
        signals = list(
            self.session.scalars(
                select(ProductRiskSignal)
                .where(
                    ProductRiskSignal.organization_id == payload.organization_id,
                    ProductRiskSignal.product_candidate_id == payload.product_candidate_id,
                    ProductRiskSignal.status != "dismissed",
                )
                .order_by(ProductRiskSignal.created_at, ProductRiskSignal.id)
            )
        )
        if not signals:
            raise IntelligenceValidationError(
                "Risk assessment requires at least one active signal."
            )
        confidence_total = sum(signal.confidence for signal in signals)
        if confidence_total == 0:
            score = 0.0
        else:
            score = round(
                sum(SEVERITY_WEIGHT[signal.severity] * signal.confidence for signal in signals)
                / confidence_total,
                2,
            )
        confidence = round(sum(signal.confidence for signal in signals) / len(signals), 4)
        inputs = {
            "signal_ids": [str(signal.id) for signal in signals],
            "signal_count": len(signals),
            "severity_weights": SEVERITY_WEIGHT,
            "excluded_status": "dismissed",
        }
        return self._save(
            ProductRiskAssessment(
                **payload.model_dump(),
                risk_score=score,
                risk_level=self.risk_level(score),
                formula_version=self.formula_version,
                assessment_inputs=inputs,
                confidence=confidence,
            )
        )

    def assess_viability(self, payload: CommercialViabilityCreate) -> CommercialViabilityAssessment:
        self._candidate(payload.product_candidate_id, payload.organization_id)
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
                "Commercial viability requires a product risk assessment."
            )
        adjusted = round(max(0.0, min(100.0, payload.opportunity_score - risk.risk_score)), 2)
        recommendation = self.recommendation(adjusted, risk.risk_score)
        reasoning = (
            f"{self.formula_version}: opportunity {payload.opportunity_score:.2f} minus "
            f"risk {risk.risk_score:.2f} yields adjusted {adjusted:.2f}; advisory "
            f"recommendation {recommendation.value.upper()} requires human decision authority."
        )
        return self._save(
            CommercialViabilityAssessment(
                **payload.model_dump(),
                risk_score=risk.risk_score,
                adjusted_score=adjusted,
                recommendation=recommendation,
                reasoning=reasoning,
            )
        )

    def scoped_signal(self, signal_id: UUID, organization_id: UUID) -> ProductRiskSignal:
        signal = self.session.get(ProductRiskSignal, signal_id)
        if signal is None or signal.organization_id != organization_id:
            raise IntelligenceScopeError("Product risk signal was not found in this organization.")
        return signal

    @staticmethod
    def risk_level(score: float) -> str:
        if score >= 75:
            return "critical"
        if score >= 50:
            return "high"
        if score >= 25:
            return "medium"
        return "low"

    @staticmethod
    def recommendation(adjusted: float, risk_score: float) -> CommercialRecommendation:
        if risk_score >= 75 or adjusted < 30:
            return CommercialRecommendation.REJECT
        if adjusted >= 70 and risk_score < 40:
            return CommercialRecommendation.GO
        if adjusted >= 50 and risk_score < 60:
            return CommercialRecommendation.TEST
        return CommercialRecommendation.REVIEW

    def _candidate(self, candidate_id: UUID, organization_id: UUID) -> ProductCandidate:
        candidate = self.session.get(ProductCandidate, candidate_id)
        if candidate is None or candidate.organization_id != organization_id:
            raise IntelligenceScopeError("Product candidate was not found in this organization.")
        return candidate

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
