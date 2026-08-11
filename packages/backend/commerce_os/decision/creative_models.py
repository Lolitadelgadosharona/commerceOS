from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CreativeStrategyStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CreativeExperimentStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"


class CreativeStrategy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_strategies"
    __table_args__ = (UniqueConstraint("product_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    marketing_objective: Mapped[str] = mapped_column(Text, nullable=False)
    core_message: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_angle: Mapped[str] = mapped_column(Text, nullable=False)
    creative_direction: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CreativeStrategyStatus] = mapped_column(String(30), nullable=False)


class CreativeHypothesis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_hypotheses"
    __table_args__ = (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    success_metric: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class CreativeBrief(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_briefs"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    story_structure: Mapped[str] = mapped_column(Text, nullable=False)
    proof_points: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(30), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    key_message: Mapped[str] = mapped_column(Text, nullable=False)
    proof_requirements: Mapped[str] = mapped_column(Text, nullable=False)
    cta_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    @property
    def creative_strategy_id(self) -> UUID:
        return self.strategy_id


class CreativeChannelFit(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_channel_fits"
    __table_args__ = (
        UniqueConstraint("product_id", "channel"),
        CheckConstraint("suitability_score BETWEEN 0 AND 100", name="suitability_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    suitability_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class CreativeExperiment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_experiments"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    hypothesis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_hypotheses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_name: Mapped[str] = mapped_column(String(250), nullable=False)
    test_objective: Mapped[str] = mapped_column(Text, nullable=False)
    metric: Mapped[str] = mapped_column(String(250), nullable=False)
    result: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CreativeExperimentStatus] = mapped_column(String(30), nullable=False)
