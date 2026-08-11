from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ChannelExecutionPlan(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_execution_plans"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    execution_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), nullable=True
    )


class CreativeChannelExperiment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_channel_experiments"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    channel_execution_plan_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("channel_execution_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    creative_variant_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    success_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    test_notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class DistributionRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "distribution_records"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    distribution_status: Mapped[str] = mapped_column(String(30), nullable=False)
    published_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), nullable=True
    )


class ChannelPerformanceObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_performance_observations"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    creative_asset_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creative_assets.id"), nullable=False, index=True
    )
    experiment_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("creative_channel_experiments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(19, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
