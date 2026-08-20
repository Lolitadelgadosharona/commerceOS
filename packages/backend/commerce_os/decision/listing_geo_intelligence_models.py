from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ListingIntelligenceRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_intelligence_runs"
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    opportunity_candidate_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("opportunity_discovery_candidates.id"), index=True
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    template_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    capability_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_model_capabilities.id"), nullable=False, index=True
    )
    prompt_version_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("prompt_versions.id"), index=True
    )
    ai_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), index=True
    )
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)


class ListingIntelligenceEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_intelligence_evidence"
    __table_args__ = (
        UniqueConstraint("listing_run_id", "evidence_type", "evidence_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="listing_intel_evidence_conf"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    listing_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("listing_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class ListingStrategyRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_strategy_recommendations"
    __table_args__ = (
        UniqueConstraint("listing_run_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="listing_strategy_rec_conf"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    listing_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("listing_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_segment: Mapped[str] = mapped_column(Text, nullable=False)
    primary_problem: Mapped[str] = mapped_column(Text, nullable=False)
    positioning: Mapped[str] = mapped_column(Text, nullable=False)
    unique_value: Mapped[str] = mapped_column(Text, nullable=False)
    benefits: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    feature_translation: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    trust_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    competitive_difference: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)


class GEOContentRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "geo_content_recommendations"
    __table_args__ = (
        UniqueConstraint("listing_run_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="geo_content_rec_conf"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    listing_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("listing_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_description: Mapped[str] = mapped_column(Text, nullable=False)
    important_attributes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    customer_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    answer_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    comparison_topics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    expert_topics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    citation_targets: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class FAQRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "faq_recommendations"
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    listing_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("listing_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    customer_intent: Mapped[str] = mapped_column(String(40), nullable=False)
    answer_outline: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    risk: Mapped[str] = mapped_column(Text, nullable=False)
