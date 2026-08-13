from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
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


class CreativeAssetType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    UGC = "ugc"
    CAROUSEL = "carousel"
    TEXT = "text"


class CreativeAsset(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_assets"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[CreativeAssetType] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False)
    production_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("creative_production_requests.id"), index=True
    )
    review_status: Mapped[str] = mapped_column(String(30), default="unreviewed", nullable=False)
    quality_score: Mapped[float | None] = mapped_column(nullable=True)


class CreativeAssetVersion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_asset_versions"
    __table_args__ = (
        CheckConstraint("version_number > 0", name="version_number_positive"),
        UniqueConstraint("asset_id", "version_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    variation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    experiment_group: Mapped[str] = mapped_column(String(100), nullable=False)


class CreativePerformanceObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_performance_observations"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    period: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
