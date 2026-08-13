from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ReplenishmentAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "replenishment_assessments"
    __table_args__ = (
        CheckConstraint("replenishment_probability BETWEEN 0 AND 1", name="probability_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("status IN ('draft','review','current','expired')", name="status_values"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    strategic_account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("strategic_account_profiles.id", ondelete="CASCADE"), index=True
    )
    product_reference: Mapped[str | None] = mapped_column(String(500))
    historical_purchase_references: Mapped[list[str]] = mapped_column(JSON)
    purchase_frequency_indicator: Mapped[float | None]
    last_purchase_date: Mapped[date | None]
    expected_replenishment_cycle_days: Mapped[int | None]
    behavior_indicators: Mapped[dict[str, Any]] = mapped_column(JSON)
    conversation_evidence: Mapped[list[str]] = mapped_column(JSON)
    estimated_next_purchase_start: Mapped[date | None]
    estimated_next_purchase_end: Mapped[date | None]
    replenishment_probability: Mapped[float | None]
    confidence: Mapped[float]
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    assessment_version: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
