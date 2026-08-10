from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
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


class AssetStrategyStatus(StrEnum):
    DRAFT = "draft"
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    ARCHIVED = "archived"


class CreativeAssetStrategy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_asset_strategies"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=False, index=True
    )
    creative_strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id"), nullable=False, index=True
    )
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_format: Mapped[str] = mapped_column(String(30), nullable=False)
    creative_angle: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[AssetStrategyStatus] = mapped_column(String(30), nullable=False)


class CreativeModelProvider(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_model_providers"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider_name", "capability_type"),
        CheckConstraint("quality_score BETWEEN 0 AND 100", name="quality_range"),
        CheckConstraint("cost_score BETWEEN 0 AND 100", name="cost_range"),
        CheckConstraint("speed_score BETWEEN 0 AND 100", name="speed_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    capability_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    cost_score: Mapped[float] = mapped_column(Float, nullable=False)
    speed_score: Mapped[float] = mapped_column(Float, nullable=False)
    availability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class CreativeRoutingDecision(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_routing_decisions"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    asset_strategy_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_asset_strategies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability_required: Mapped[str] = mapped_column(String(30), nullable=False)
    selected_provider_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_model_providers.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    factor_snapshot: Mapped[dict[str, float | None]] = mapped_column(JSON, nullable=False)
    routing_score: Mapped[float] = mapped_column(Float, nullable=False)
    router_version: Mapped[str] = mapped_column(String(40), nullable=False)


class CreativeEconomicAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_economic_assessments"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("profitability_score BETWEEN 0 AND 100", name="profitability_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id"), nullable=False, index=True
    )
    estimated_production_cost: Mapped[float] = mapped_column(Float, nullable=False)
    expected_impact: Mapped[float] = mapped_column(Float, nullable=False)
    test_value: Mapped[float] = mapped_column(Float, nullable=False)
    profitability_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)


class CreativePatternReference(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_pattern_references"
    __table_args__ = (UniqueConstraint("organization_id", "name", "pattern_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    performance_notes: Mapped[str] = mapped_column(Text, nullable=False)
