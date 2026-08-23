from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class DailyRevenueRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "daily_revenue_runs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "revenue_experiment_id",
            "run_date",
            "industry",
            "target_geography",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    revenue_experiment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_experiments.id"), index=True
    )
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    target_geography: Mapped[str] = mapped_column(String(240), nullable=False)
    generated_prospects: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


class DailyRevenueRunProspect(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "daily_revenue_run_prospects"
    __table_args__ = (UniqueConstraint("daily_revenue_run_id", "prospect_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    daily_revenue_run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("daily_revenue_runs.id"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    priority_score: Mapped[float | None] = mapped_column(Float)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)


class FounderActionItem(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "founder_action_items"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    revenue_experiment_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("revenue_experiments.id"), index=True
    )
    prospect_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_prospects.id"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_reference_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    assigned_to: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")


class GrowthExternalDataConnector(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_external_data_connectors"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), nullable=False)
    collection_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    credential_reference: Mapped[str | None] = mapped_column(String(500))
    configuration_metadata: Mapped[dict[str, Any]] = mapped_column(
        "configuration", JSON, nullable=False
    )
    policy_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")


class CustomerServiceDelivery(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_service_deliveries"
    __table_args__ = (UniqueConstraint("organization_id", "offer_tracking_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    offer_tracking_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_offer_tracking.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned")
    owner_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    customer_feedback_reference: Mapped[str | None] = mapped_column(String(500))


class CustomerDeliveryItem(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_delivery_items"
    __table_args__ = (UniqueConstraint("delivery_id", "sequence"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    delivery_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_service_deliveries.id"), index=True
    )
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
