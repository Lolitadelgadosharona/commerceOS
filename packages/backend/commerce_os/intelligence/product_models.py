from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProductHypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ProductRiskType(StrEnum):
    TRADEMARK = "trademark"
    PATENT = "patent"
    BRAND = "brand"
    POLICY = "policy"
    DISPUTE = "dispute"
    QUALITY = "quality"


class ProductRiskStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


class ProductHypothesis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_hypotheses"
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    customer_problem: Mapped[str] = mapped_column(Text, nullable=False)
    solution_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_customer: Mapped[str] = mapped_column(String(500), nullable=False)
    target_market: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[ProductHypothesisStatus] = mapped_column(String(30), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class ProductEconomics(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_economics"
    __table_args__ = (
        UniqueConstraint("product_id"),
        CheckConstraint("selling_price > 0", name="selling_price_positive"),
        CheckConstraint("estimated_product_cost >= 0", name="product_cost_nonnegative"),
        CheckConstraint("estimated_shipping_cost >= 0", name="shipping_cost_nonnegative"),
        CheckConstraint("payment_cost >= 0", name="payment_cost_nonnegative"),
        CheckConstraint("estimated_marketing_cost >= 0", name="marketing_cost_nonnegative"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selling_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    estimated_product_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    estimated_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    estimated_marketing_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contribution_margin: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    margin_percentage: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)


class ProductEconomicInputProvenance(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_economic_input_provenance"
    __table_args__ = (
        UniqueConstraint("product_economics_id", "metric"),
        CheckConstraint("value IS NULL OR value >= 0", name="value_nonnegative"),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="confidence_range",
        ),
        CheckConstraint(
            "(classification = 'unknown' AND value IS NULL) OR "
            "(classification <> 'unknown' AND value IS NOT NULL)",
            name="unknown_value_semantics",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_economics_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_economics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_quote_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("supplier_quotes.id", ondelete="SET NULL"), index=True
    )
    metric: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class SupplierCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_candidates"
    __table_args__ = (UniqueConstraint("product_id", "source_type", "supplier_reference"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time: Mapped[str] = mapped_column(String(200), nullable=False)
    quality_notes: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)


class ProductRisk(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_risks"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_type: Mapped[ProductRiskType] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProductRiskStatus] = mapped_column(String(30), nullable=False)


class ProductInvestmentScore(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_investment_scores"
    __table_args__ = (
        UniqueConstraint("product_id"),
        CheckConstraint("opportunity_score BETWEEN 0 AND 100", name="opportunity_range"),
        CheckConstraint("margin_score BETWEEN 0 AND 100", name="margin_range"),
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint("competition_score BETWEEN 0 AND 100", name="competition_range"),
        CheckConstraint("confidence_score BETWEEN 0 AND 100", name="confidence_range"),
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="overall_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    margin_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(30), nullable=False)
