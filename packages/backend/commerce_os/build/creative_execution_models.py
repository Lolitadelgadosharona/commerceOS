from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin, utc_now


class CreativeExecutionRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_execution_records"
    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="estimated_cost_nonnegative"),
        CheckConstraint("actual_cost IS NULL OR actual_cost >= 0", name="actual_cost_nonnegative"),
        CheckConstraint("duration >= 0", name="duration_nonnegative"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    generation_job_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_provider_capabilities.id"), nullable=False, index=True
    )
    execution_status: Mapped[str] = mapped_column(String(30), nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(19, 6), nullable=True)
    duration: Mapped[float] = mapped_column(nullable=False)


class CreativeArtifact(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_artifacts"
    __table_args__ = (UniqueConstraint("generation_job_id", "asset_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    generation_job_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    artifact_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(30), nullable=False)
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


class CreativeGenerationCostObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_generation_cost_observations"
    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="est_nonneg"),
        CheckConstraint("actual_cost >= 0", name="act_nonneg"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    provider_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_provider_capabilities.id"), nullable=False, index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    actual_cost: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
