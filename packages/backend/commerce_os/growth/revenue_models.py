from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
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


class GrowthProspect(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_prospects"
    __table_args__ = (UniqueConstraint("organization_id", "website", "business_name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    business_name: Mapped[str] = mapped_column(String(250), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(320))
    social_links: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    location: Mapped[str | None] = mapped_column(String(250))
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    business_type: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="discovered")


class GrowthProspectEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_prospect_evidence"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_evidence_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_prospects.id", ondelete="CASCADE"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GrowthOpportunityAnalysis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_opportunity_analyses"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_opp_conf_range"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    customer_impact: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    recommended_offer: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    ai_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), index=True
    )


class GrowthGift(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_gifts"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_opportunity_analyses.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    before_state: Mapped[str] = mapped_column(Text, nullable=False)
    after_state: Mapped[str] = mapped_column(Text, nullable=False)
    asset_reference: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )


class GrowthOutreachDraft(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_outreach_drafts"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    growth_gift_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_gifts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_used: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    ai_request_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ai_requests.id"), index=True)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), index=True
    )


class SalesConversationAnalysis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "sales_conversation_analyses"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    conversation_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    intent: Mapped[str] = mapped_column(String(40), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(40), nullable=False)
    objection: Mapped[str | None] = mapped_column(Text)
    buying_stage: Mapped[str] = mapped_column(String(80), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_reply: Mapped[str] = mapped_column(Text, nullable=False)
    ai_request_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ai_requests.id"), index=True)


class AIModelPolicy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_model_policies"
    __table_args__ = (UniqueConstraint("organization_id", "task_type"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_model: Mapped[str] = mapped_column(String(200), nullable=False)
    fallback_model: Mapped[str | None] = mapped_column(String(200))
    quality_requirement: Mapped[str] = mapped_column(String(50), nullable=False)


@event.listens_for(GrowthProspectEvidence, "before_update")
def _prevent_evidence_update(*_: object) -> None:
    raise ValueError("Growth prospect evidence is immutable.")
