from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, String, Text, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class GrowthObjectionRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_objection_records"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("sales_conversation_analyses.id", ondelete="CASCADE"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    objection_type: Mapped[str] = mapped_column(String(40), nullable=False)
    customer_segment: Mapped[str] = mapped_column(String(250), nullable=False)
    original_message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_response: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)


class GrowthSalesLearningSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_sales_learning_signals"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("sales_conversation_analyses.id"), index=True
    )
    objection_record_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_objection_records.id"), index=True
    )
    learning_observation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("learning_observations.id"), unique=True, index=True
    )
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    future_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class GrowthMessagePerformanceObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_message_performance_observations"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    outreach_draft_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_outreach_drafts.id"), index=True
    )
    prospect_experiment_link_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("prospect_experiment_links.id"), index=True
    )
    customer_segment: Mapped[str] = mapped_column(String(250), nullable=False)
    message_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    observation_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


@event.listens_for(GrowthMessagePerformanceObservation, "before_update")
@event.listens_for(GrowthMessagePerformanceObservation, "before_delete")
def _protect_message_performance(*_: object) -> None:
    raise ValueError("Message performance observations are append-only.")
