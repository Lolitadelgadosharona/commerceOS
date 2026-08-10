from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Date, Float, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class FinancialPeriod(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "financial_periods"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="valid_date_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class RevenueObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "revenue_observations"
    __table_args__ = (CheckConstraint("amount >= 0", name="nonnegative_amount"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    channel: Mapped[str | None] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)


class CostObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "cost_observations"
    __table_args__ = (CheckConstraint("amount >= 0", name="nonnegative_amount"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, index=True
    )
    channel: Mapped[str | None] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)


class ContributionProfitAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "contribution_profit_assessments"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, index=True
    )
    period_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("financial_periods.id"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    contribution_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    margin_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    component_snapshot: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)


class UnitEconomicAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "unit_economic_assessments"
    __table_args__ = (
        CheckConstraint("gross_margin BETWEEN 0 AND 1", name="gross_margin_range"),
        CheckConstraint("refund_rate BETWEEN 0 AND 1", name="refund_rate_range"),
        CheckConstraint("dispute_rate BETWEEN 0 AND 1", name="dispute_rate_range"),
        CheckConstraint("profitability_score BETWEEN 0 AND 100", name="profitability_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, index=True
    )
    average_order_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    customer_acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gross_margin: Mapped[float] = mapped_column(Float, nullable=False)
    refund_rate: Mapped[float] = mapped_column(Float, nullable=False)
    dispute_rate: Mapped[float] = mapped_column(Float, nullable=False)
    lifetime_value_estimate: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    profitability_score: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)


class FinancialRiskSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "financial_risk_signals"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    period_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("financial_periods.id"))
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"))
    risk_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)
