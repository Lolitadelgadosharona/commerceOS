from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class RevenueExperiment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "revenue_experiments"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_segment: Mapped[str] = mapped_column(Text, nullable=False)
    offer_type: Mapped[str] = mapped_column(String(120), nullable=False)
    message_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


class ProspectExperimentLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_experiment_links"
    __table_args__ = (UniqueConstraint("experiment_id", "prospect_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_experiments.id", ondelete="CASCADE"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    assigned_offer: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_message: Mapped[str] = mapped_column(Text, nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False)


class OutreachTrackingEvent(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "outreach_tracking_events"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_experiment_link_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_experiment_links.id", ondelete="CASCADE"), index=True
    )
    outreach_draft_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_outreach_drafts.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


@event.listens_for(OutreachTrackingEvent, "before_update")
@event.listens_for(OutreachTrackingEvent, "before_delete")
def _protect_outreach_event(*_: object) -> None:
    raise ValueError("Outreach tracking events are append-only.")
