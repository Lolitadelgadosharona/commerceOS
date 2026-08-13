from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CustomerJourneyEvent(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_journey_events"
    __table_args__ = (UniqueConstraint("organization_id", "source", "reference_id", "event_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_link_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("customer_identity_links.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    reference_id: Mapped[str] = mapped_column(nullable=False)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Customer360Profile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_360_profiles"
    __table_args__ = (UniqueConstraint("organization_id", "customer_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    conversation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    journey_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    risk_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    value_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
