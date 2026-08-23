from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class DailyExperimentWorkspaceItem(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "daily_experiment_workspace_items"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "workspace_date", "revenue_experiment_id", "prospect_id"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    workspace_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    revenue_experiment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_experiments.id"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    daily_opportunity_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("daily_growth_opportunities.id"), index=True
    )
    diagnosis_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_diagnoses.id"), index=True
    )
    growth_gift_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_gifts.id"), index=True
    )
    offer_recommendation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_offer_recommendations.id"), index=True
    )
    priority: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_review")
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


class EmailWorkflowReference(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "email_workflow_references"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    outreach_draft_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_outreach_drafts.id"), index=True
    )
    email_account_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    draft_reference: Mapped[str | None] = mapped_column(String(500))
    thread_reference: Mapped[str | None] = mapped_column(String(500))
    inbound_reply_reference: Mapped[str | None] = mapped_column(String(500))
    reference_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    recorded_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


class GrowthCustomerFeedback(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_customer_feedback"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_feedback_conf"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    revenue_experiment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("revenue_experiments.id"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    conversation_analysis_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("sales_conversation_analyses.id"), index=True
    )
    customer_response: Mapped[str] = mapped_column(Text, nullable=False)
    interest_level: Mapped[str] = mapped_column(String(30), nullable=False)
    objection_category: Mapped[str | None] = mapped_column(String(80))
    reason_lost: Mapped[str | None] = mapped_column(Text)
    reason_won: Mapped[str | None] = mapped_column(Text)
    learning_signal: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    learning_observation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("learning_observations.id"), unique=True, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


@event.listens_for(EmailWorkflowReference, "before_update")
@event.listens_for(EmailWorkflowReference, "before_delete")
def _protect_email_reference(*_: object) -> None:
    raise ValueError("Email workflow references are append-only.")
