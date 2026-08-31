from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.opportunity_models import OpportunityScore
from commerce_os.intelligence.opportunity_services import _get_scoped_opportunity
from commerce_os.intelligence.product_models import (
    ProductEconomicInputProvenance,
    ProductEconomics,
    ProductHypothesis,
    ProductInvestmentScore,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.intelligence.product_schemas import (
    ProductEconomicInputCreate,
    ProductEconomicsCreate,
    ProductHypothesisCreate,
    ProductInvestmentScoreCreate,
    ProductRiskCreate,
    SupplierCandidateCreate,
)

FORMULA_VERSION = "v1.0"
SEVERITY_SCORE = {"low": 25.0, "medium": 50.0, "high": 75.0, "critical": 100.0}


def _get_scoped_product(
    session: Session, product_id: UUID, organization_id: UUID
) -> ProductHypothesis:
    product = session.get(ProductHypothesis, product_id)
    if product is None:
        raise IntelligenceNotFoundError("Product hypothesis was not found.")
    if product.organization_id != organization_id:
        raise IntelligenceScopeError("Product hypothesis belongs to another organization.")
    return product


class ProductHypothesisService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductHypothesisCreate) -> ProductHypothesis:
        _get_scoped_opportunity(self.session, payload.opportunity_id, payload.organization_id)
        product = ProductHypothesis(**payload.model_dump())
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product


class ProductEconomicsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def calculate(payload: ProductEconomicsCreate) -> tuple[Decimal, Decimal]:
        contribution = (
            payload.selling_price
            - payload.estimated_product_cost
            - payload.estimated_shipping_cost
            - payload.payment_cost
            - payload.estimated_marketing_cost
        )
        contribution = contribution.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        percentage = (contribution / payload.selling_price * Decimal(100)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        return contribution, percentage

    def upsert(self, payload: ProductEconomicsCreate) -> ProductEconomics:
        _get_scoped_product(self.session, payload.product_id, payload.organization_id)
        economics = self.session.scalar(
            select(ProductEconomics).where(ProductEconomics.product_id == payload.product_id)
        )
        values = payload.model_dump()
        values["contribution_margin"], values["margin_percentage"] = self.calculate(payload)
        if economics is None:
            economics = ProductEconomics(**values)
            self.session.add(economics)
        else:
            for field, value in values.items():
                setattr(economics, field, value)
        self.session.commit()
        self.session.refresh(economics)
        return economics

    def upsert_input(self, payload: ProductEconomicInputCreate) -> ProductEconomicInputProvenance:
        economics = self.session.get(ProductEconomics, payload.product_economics_id)
        if economics is None:
            raise IntelligenceNotFoundError("Product economics record was not found.")
        if economics.organization_id != payload.organization_id:
            raise IntelligenceScopeError("Product economics belongs to another organization.")
        item = self.session.scalar(
            select(ProductEconomicInputProvenance).where(
                ProductEconomicInputProvenance.product_economics_id == economics.id,
                ProductEconomicInputProvenance.metric == payload.metric,
            )
        )
        values = payload.model_dump()
        if item is None:
            item = ProductEconomicInputProvenance(**values)
            self.session.add(item)
        else:
            for field, value in values.items():
                setattr(item, field, value)
        self.session.commit()
        self.session.refresh(item)
        return item


class SupplierCandidateService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SupplierCandidateCreate) -> SupplierCandidate:
        _get_scoped_product(self.session, payload.product_id, payload.organization_id)
        candidate = SupplierCandidate(**payload.model_dump())
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate


class ProductRiskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductRiskCreate) -> ProductRisk:
        _get_scoped_product(self.session, payload.product_id, payload.organization_id)
        risk = ProductRisk(**payload.model_dump())
        self.session.add(risk)
        self.session.commit()
        self.session.refresh(risk)
        return risk


class ProductInvestmentScoringService:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def calculate(
        opportunity: float, margin: float, risk: float, competition: float, confidence: float
    ) -> float:
        result = (
            opportunity * 0.35
            + margin * 0.25
            + (100 - risk) * 0.15
            + (100 - competition) * 0.15
            + confidence * 0.10
        )
        return round(max(0, min(100, result)), 2)

    def score(self, payload: ProductInvestmentScoreCreate) -> ProductInvestmentScore:
        product = _get_scoped_product(self.session, payload.product_id, payload.organization_id)
        opportunity = self.session.scalar(
            select(OpportunityScore).where(
                OpportunityScore.opportunity_id == product.opportunity_id
            )
        )
        economics = self.session.scalar(
            select(ProductEconomics).where(ProductEconomics.product_id == product.id)
        )
        if opportunity is None or economics is None:
            raise IntelligenceValidationError(
                "An opportunity score and product economics are required before investment scoring."
            )
        risks = self.session.scalars(
            select(ProductRisk).where(
                ProductRisk.product_id == product.id, ProductRisk.status == "open"
            )
        ).all()
        risk_score = max((SEVERITY_SCORE[str(risk.severity)] for risk in risks), default=0.0)
        margin_score = max(0.0, min(100.0, float(economics.margin_percentage)))
        confidence_score = product.confidence_score * 100
        values = {
            "organization_id": payload.organization_id,
            "product_id": product.id,
            "opportunity_score": opportunity.overall_score,
            "margin_score": margin_score,
            "risk_score": risk_score,
            "competition_score": payload.competition_score,
            "confidence_score": confidence_score,
            "overall_score": self.calculate(
                opportunity.overall_score,
                margin_score,
                risk_score,
                payload.competition_score,
                confidence_score,
            ),
            "formula_version": FORMULA_VERSION,
        }
        score = self.session.scalar(
            select(ProductInvestmentScore).where(ProductInvestmentScore.product_id == product.id)
        )
        if score is None:
            score = ProductInvestmentScore(**values)
            self.session.add(score)
        else:
            for field, value in values.items():
                setattr(score, field, value)
        self.session.commit()
        self.session.refresh(score)
        return score
