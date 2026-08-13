from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CustomerExpansionOpportunity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_expansion_opportunities"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("risk_indicator BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint(
            "status IN ('identified','review','ready','dismissed','expired')", name="status_values"
        ),
    )
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    strategic_account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("strategic_account_profiles.id", ondelete="CASCADE"), index=True
    )
    opportunity_type: Mapped[str] = mapped_column(String(40))
    product_reference: Mapped[str | None] = mapped_column(String(500))
    estimated_value_indicator: Mapped[float | None]
    confidence: Mapped[float]
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    risk_indicator: Mapped[float]
    status: Mapped[str] = mapped_column(String(30))


class CustomerNextBestAction(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_next_best_actions"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("priority IN ('low','normal','high','critical')", name="priority_values"),
        CheckConstraint(
            "status IN ('draft','reviewed','accepted','rejected')", name="status_values"
        ),
    )
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    strategic_account_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("strategic_account_profiles.id", ondelete="SET NULL")
    )
    recommendation_type: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    evidence_references: Mapped[list[str]] = mapped_column(JSON)
    priority: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float]
    recommended_time_window: Mapped[date | None]
    human_review_required: Mapped[bool]
    status: Mapped[str] = mapped_column(String(30))
    formula_or_rule_version: Mapped[str] = mapped_column(String(50))
    decision_queue_item_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("decision_queue_items.id")
    )


class StrategicAccountScore(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "strategic_account_scores"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    strategic_account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("strategic_account_profiles.id", ondelete="CASCADE"), index=True
    )
    input_values: Mapped[dict[str, float | None]] = mapped_column(JSON)
    weights: Mapped[dict[str, float]] = mapped_column(JSON)
    formula_version: Mapped[str] = mapped_column(String(50))
    score: Mapped[float]
    confidence: Mapped[float]
    evidence_coverage: Mapped[float]
