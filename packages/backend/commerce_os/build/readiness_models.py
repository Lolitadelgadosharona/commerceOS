from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class SupplierCandidatePromotion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_candidate_promotions"
    __table_args__ = (UniqueConstraint("organization_id", "supplier_candidate_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    supplier_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_candidates.id"), index=True
    )
    supplier_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("supplier_profiles.id"), index=True
    )
    confirmed_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProductBuildRequirement(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_build_requirements"
    __table_args__ = (UniqueConstraint("product_truth_id", "attribute_key"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    product_truth_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_truth.id", ondelete="CASCADE"), index=True
    )
    attribute_key: Mapped[str] = mapped_column(String(100))
    display_label: Mapped[str] = mapped_column(String(200))
    value: Mapped[object | None] = mapped_column(JSON)
    unit: Mapped[str | None] = mapped_column(String(50))
    classification: Mapped[str] = mapped_column(String(30))
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    required_for_build: Mapped[bool] = mapped_column(Boolean, default=True)
    required_for_listing: Mapped[bool] = mapped_column(Boolean, default=False)


class BuildRequirementPolicy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "build_requirement_policies"
    __table_args__ = (UniqueConstraint("organization_id", "product_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    sample_required: Mapped[bool] = mapped_column(Boolean, default=False)
    inspection_required: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_evidence_required: Mapped[bool] = mapped_column(Boolean, default=False)
    packaging_validation_required: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text)


class ProductSample(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_samples"
    __table_args__ = (UniqueConstraint("organization_id", "sample_identifier"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("supplier_profiles.id"), index=True)
    approved_product_supplier_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approved_product_suppliers.id"), index=True
    )
    sample_identifier: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), default="not_requested")
    requested_at: Mapped[date | None] = mapped_column(Date)
    received_at: Mapped[date | None] = mapped_column(Date)
    sample_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    version_reference: Mapped[str | None] = mapped_column(String(250))
    notes: Mapped[str | None] = mapped_column(Text)
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    recorded_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    review_status: Mapped[str] = mapped_column(String(30), default="unknown")
    review_dimensions: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupplierValidationArtifact(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "supplier_validation_artifacts"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    supplier_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("supplier_profiles.id"), index=True)
    sample_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("product_samples.id", ondelete="SET NULL"), index=True
    )
    validation_type: Mapped[str] = mapped_column(String(50))
    classification: Mapped[str] = mapped_column(String(30))
    result: Mapped[str] = mapped_column(String(30))
    observations: Mapped[str] = mapped_column(Text)
    critical_defects: Mapped[int | None] = mapped_column()
    major_defects: Mapped[int | None] = mapped_column()
    minor_defects: Mapped[int | None] = mapped_column()
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    verified_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    observed_at: Mapped[date | None] = mapped_column(Date)
