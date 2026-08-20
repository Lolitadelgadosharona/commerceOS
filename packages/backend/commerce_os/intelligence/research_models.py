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


class ResearchAnalysis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "research_analyses"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    ai_request_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), nullable=False, index=True
    )
    analysis_type: Mapped[str] = mapped_column(String(60), nullable=False)
    output_classification: Mapped[str] = mapped_column(String(30), nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


class ResearchEvidenceCitation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "research_evidence_citations"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id", "evidence_type", "evidence_id", name="uq_research_citation_evidence"
        ),
        CheckConstraint("relevance_score BETWEEN 0 AND 1", name="relevance_score_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    citation_note: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    citation_location: Mapped[str | None] = mapped_column(String(500))
    methodology_version: Mapped[str | None] = mapped_column(String(80))
    missing_evidence: Mapped[bool] = mapped_column(nullable=False, default=False)


class ResearchRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "research_runs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"), index=True)
    research_type: Mapped[str] = mapped_column(String(60), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    capability_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_model_capabilities.id"), nullable=False, index=True
    )
    prompt_version_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("prompt_versions.id"), index=True
    )
    ai_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), index=True
    )
    analysis_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("research_analyses.id"), index=True
    )
    decision_queue_item_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("decision_queue_items.id"), index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)


class ResearchRunEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "research_run_evidence"
    __table_args__ = (
        UniqueConstraint("research_run_id", "evidence_type", "evidence_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="research_run_evidence_confidence"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    research_run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class CustomerPainResearch(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_pain_research"
    __table_args__ = (UniqueConstraint("analysis_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_analyses.id"), nullable=False, index=True
    )
    pain_patterns: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    customer_needs: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    motivations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    language_themes: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class MarketInsightResearch(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_insight_research"
    __table_args__ = (UniqueConstraint("analysis_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_analyses.id"), nullable=False, index=True
    )
    market_trends: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    emerging_signals: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    competitive_observations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    opportunity_indicators: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class OpportunityResearchBrief(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_research_briefs"
    __table_args__ = (UniqueConstraint("analysis_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_analyses.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id"), nullable=False, index=True
    )
    opportunity_summary: Mapped[str] = mapped_column(Text, nullable=False)
    customer_problem: Mapped[str] = mapped_column(Text, nullable=False)
    market_context: Mapped[str] = mapped_column(Text, nullable=False)
    competition: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    economics_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
