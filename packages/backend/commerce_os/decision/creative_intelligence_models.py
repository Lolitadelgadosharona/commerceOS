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


class CreativeIntelligenceRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_intelligence_runs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_candidate_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("opportunity_discovery_candidates.id"), index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
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


class CreativeIntelligenceEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_intelligence_evidence"
    __table_args__ = (
        UniqueConstraint("creative_run_id", "evidence_type", "evidence_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="creative_intel_evidence_conf"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class CreativeStrategyRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_strategy_recommendations"
    __table_args__ = (
        UniqueConstraint("creative_run_id"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="creative_strategy_rec_conf"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_customer: Mapped[str] = mapped_column(Text, nullable=False)
    customer_problem: Mapped[str] = mapped_column(Text, nullable=False)
    core_message: Mapped[str] = mapped_column(Text, nullable=False)
    value_proposition: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_angle: Mapped[str] = mapped_column(Text, nullable=False)
    rational_angle: Mapped[str] = mapped_column(Text, nullable=False)
    trust_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    channel_recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    estimated_impact: Mapped[str | None] = mapped_column(Text)
    output_type: Mapped[str] = mapped_column(String(20), nullable=False)


class CreativeAngle(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_angles"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="creative_angle_conf"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    angle_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)


class CreativeBriefRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "creative_brief_recommendations"
    __table_args__ = (UniqueConstraint("creative_run_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    creative_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("creative_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    proof: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    visual_direction: Mapped[str] = mapped_column(Text, nullable=False)
    video_concept: Mapped[str] = mapped_column(Text, nullable=False)
    image_concept: Mapped[str] = mapped_column(Text, nullable=False)
    ugc_concept: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
