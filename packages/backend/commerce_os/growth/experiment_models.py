from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
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


class GrowthCreativeExperiment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_creative_experiments"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    creative_strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id"), nullable=False, index=True
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )


class ExperimentVariant(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_experiment_variants"
    __table_args__ = (UniqueConstraint("experiment_id", "variant_name"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("growth_creative_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    variant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)


class DistributionCampaign(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "distribution_campaigns"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("growth_creative_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    approval_state: Mapped[str] = mapped_column(String(20), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )


class GrowthPerformanceObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_performance_observations"
    __table_args__ = (
        CheckConstraint("impressions >= 0", name="impressions_nonnegative"),
        CheckConstraint("clicks >= 0", name="clicks_nonnegative"),
        CheckConstraint("engagement >= 0", name="engagement_nonnegative"),
        CheckConstraint("conversion >= 0", name="conversion_nonnegative"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("growth_creative_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    conversion: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    revenue_observation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("revenue_observations.id"), index=True
    )
    confidence: Mapped[float] = mapped_column(nullable=False)


class GrowthLearningSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_learning_signals"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_experiment_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("growth_creative_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pattern_reference_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("creative_pattern_references.id"), index=True
    )
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)


class GrowthLearningObservationLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_learning_observation_links"
    __table_args__ = (UniqueConstraint("learning_signal_id", "observation_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    learning_signal_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("growth_learning_signals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_performance_observations.id"), nullable=False, index=True
    )
