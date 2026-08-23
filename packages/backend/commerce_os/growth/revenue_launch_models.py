from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProspectRevenuePipeline(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_revenue_pipelines"
    __table_args__ = (UniqueConstraint("organization_id", "prospect_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    stage: Mapped[str] = mapped_column(String(30), nullable=False, default="new_prospect")
    owner_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class RevenueOfferTracking(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "revenue_offer_tracking"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    recommendation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_offer_recommendations.id"), index=True
    )
    offer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    customer_response: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="recommended")


class PaymentReadinessRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "payment_readiness_records"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    offer_tracking_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_offer_tracking.id"), index=True
    )
    payment_provider_reference: Mapped[str | None] = mapped_column(String(500))
    payment_link: Mapped[str | None] = mapped_column(String(1000))
    invoice_reference: Mapped[str | None] = mapped_column(String(500))
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_requested")
    revenue_observation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("revenue_observations.id"), index=True
    )


class CustomerLifecycleEvent(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_lifecycle_events"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    lifecycle_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    recorded_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


@event.listens_for(CustomerLifecycleEvent, "before_update")
@event.listens_for(CustomerLifecycleEvent, "before_delete")
def _protect_lifecycle_event(*_: object) -> None:
    raise ValueError("Customer lifecycle events are append-only.")
