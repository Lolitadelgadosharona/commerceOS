from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProfitScenario(StrEnum):
    CONSERVATIVE = "conservative"
    BASE = "base"
    OPTIMISTIC = "optimistic"


class ProfitRecommendation(StrEnum):
    GO = "go"
    TEST = "test"
    REVIEW = "review"
    REJECT = "reject"


class ProductEconomicProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_economic_profiles"
    __table_args__ = (
        CheckConstraint("product_cost >= 0", name="product_cost_nonnegative"),
        CheckConstraint("shipping_cost >= 0", name="shipping_cost_nonnegative"),
        CheckConstraint("packaging_cost >= 0", name="packaging_cost_nonnegative"),
        CheckConstraint("transaction_cost >= 0", name="transaction_cost_nonnegative"),
        CheckConstraint("estimated_acquisition_cost >= 0", name="acquisition_nonnegative"),
        CheckConstraint("refund_rate_assumption BETWEEN 0 AND 1", name="refund_rate_range"),
        CheckConstraint("dispute_rate_assumption BETWEEN 0 AND 1", name="dispute_rate_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    packaging_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    transaction_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    estimated_acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    refund_rate_assumption: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)
    dispute_rate_assumption: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)


class ProductProfitAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_profit_assessments"
    __table_args__ = (
        CheckConstraint("selling_price > 0", name="selling_price_positive"),
        CheckConstraint("margin_score BETWEEN 0 AND 100", name="margin_score_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selling_price: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    gross_margin: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    contribution_profit: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    margin_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(7, 6), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)


class ProfitScenarioAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "profit_scenario_assessments"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario: Mapped[ProfitScenario] = mapped_column(String(20), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    margin: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False)


class RiskAdjustedProfitAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "risk_adjusted_profit_assessments"
    __table_args__ = tuple(
        CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
        for field, name in {
            "opportunity_score": "opportunity_range",
            "risk_score": "risk_range",
            "profit_score": "profit_range",
            "final_score": "final_range",
        }.items()
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    profit_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    final_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    recommendation: Mapped[ProfitRecommendation] = mapped_column(String(20), nullable=False)
