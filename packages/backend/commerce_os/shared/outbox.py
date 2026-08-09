from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, Session, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.events import BusinessEventEnvelope
from commerce_os.shared.models import IdMixin, TimestampMixin, utc_now


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key"),
        Index("ix_outbox_events_status_occurred_at", "status", "occurred_at"),
    )

    event_id: Mapped[UUID] = mapped_column(Uuid, unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    causation_id: Mapped[UUID | None] = mapped_column(Uuid)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    project_id: Mapped[UUID | None] = mapped_column(Uuid)
    product_id: Mapped[UUID | None] = mapped_column(Uuid)
    customer_id: Mapped[UUID | None] = mapped_column(Uuid)
    schema_version: Mapped[int] = mapped_column(nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, native_enum=False), default=OutboxStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    @classmethod
    def from_envelope(cls, event: BusinessEventEnvelope) -> "OutboxEvent":
        data = event.model_dump(mode="python")
        return cls(**data)


def add_to_outbox(session: Session, event: BusinessEventEnvelope) -> OutboxEvent:
    record = OutboxEvent.from_envelope(event)
    session.add(record)
    return record
