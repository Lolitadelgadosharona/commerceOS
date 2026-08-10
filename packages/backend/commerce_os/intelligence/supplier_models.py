from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
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
