from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
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


class SupplierProfileStatus(StrEnum):
    DISCOVERED = "discovered"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class SupplierRiskType(StrEnum):
    QUALITY = "quality"
    DELIVERY = "delivery"
    COMPLIANCE = "compliance"
    COUNTERFEIT = "counterfeit"
    CAPACITY = "capacity"
    COMMUNICATION = "communication"


class SupplierProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_profiles"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    certifications: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[SupplierProfileStatus] = mapped_column(String(30), nullable=False)


class SupplierEvaluation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_evaluations"
    __table_args__ = tuple(
        CheckConstraint(f"{name} BETWEEN 0 AND 100", name=f"{name.removesuffix('_score')}_range")
        for name in (
            "quality_score",
            "price_score",
            "lead_time_score",
            "communication_score",
            "compliance_score",
            "overall_score",
        )
    ) + (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    price_score: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_score: Mapped[float] = mapped_column(Float, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False)
    compliance_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(30), nullable=False)


class SupplierRisk(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_risks"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_type: Mapped[SupplierRiskType] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class ProductSupplierMatch(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_supplier_matches"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id"),
        CheckConstraint("match_score BETWEEN 0 AND 100", name="match_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommended: Mapped[bool] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class SupplierDecisionRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_decision_records"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)


class SupplierEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_evidence"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[object | None] = mapped_column(JSON)
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class SupplierQuote(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_quotes"
    __table_args__ = (
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="unit_price_nonnegative"),
        CheckConstraint(
            "minimum_order_quantity IS NULL OR minimum_order_quantity >= 1", name="moq_positive"
        ),
        CheckConstraint("sample_cost IS NULL OR sample_cost >= 0", name="sample_cost_nonnegative"),
        CheckConstraint(
            "tooling_cost IS NULL OR tooling_cost >= 0", name="tooling_cost_nonnegative"
        ),
        CheckConstraint(
            "packaging_cost IS NULL OR packaging_cost >= 0", name="packaging_cost_nonnegative"
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    minimum_order_quantity: Mapped[int | None] = mapped_column(Integer)
    price_tiers: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    sample_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    tooling_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    packaging_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    incoterm: Mapped[str | None] = mapped_column(String(30))
    payment_terms: Mapped[str | None] = mapped_column(String(250))
    lead_time: Mapped[str | None] = mapped_column(String(200))
    quote_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)


class ApprovedProductSupplier(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "approved_product_suppliers"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id"),
        UniqueConstraint("approval_request_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_candidate_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("supplier_candidates.id", ondelete="SET NULL"), index=True
    )
    approval_request_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
