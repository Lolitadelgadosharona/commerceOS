from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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


class GenerationRequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CreativeGenerationRequest(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_generation_requests"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_brief_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_briefs.id"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    generation_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    requested_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[GenerationRequestStatus] = mapped_column(String(30), nullable=False)


class CreativeProviderCapability(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_provider_capabilities"
    __table_args__ = (UniqueConstraint("organization_id", "provider_name", "provider_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(30), nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    cost_model: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class CreativeGenerationJob(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_generation_jobs"
    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="estimated_cost_nonnegative"),
        CheckConstraint("actual_cost IS NULL OR actual_cost >= 0", name="actual_cost_nonnegative"),
        CheckConstraint("latency IS NULL OR latency >= 0", name="latency_nonnegative"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    request_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_generation_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_provider_capabilities.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    input_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    output_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(19, 6), nullable=True)
    latency: Mapped[float | None] = mapped_column(nullable=True)


class CreativeQualityReview(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_quality_reviews"
    __table_args__ = (CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    issues: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
