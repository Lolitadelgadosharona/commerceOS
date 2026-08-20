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


class OpportunityDiscoveryRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_discovery_runs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"), index=True)
    discovery_type: Mapped[str] = mapped_column(String(60), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    research_run_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("research_runs.id"), index=True
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
    created_by: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)


class OpportunityDiscoveryEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_discovery_evidence"
    __table_args__ = (
        UniqueConstraint("discovery_run_id", "evidence_type", "evidence_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="disc_evidence_conf"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    discovery_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("opportunity_discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class OpportunityCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_discovery_candidates"
    __table_args__ = (
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="disc_candidate_conf"),
        CheckConstraint("advisory_score BETWEEN 0 AND 100", name="disc_candidate_score"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    discovery_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("opportunity_discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    customer_segment: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    solution_direction: Mapped[str] = mapped_column(Text, nullable=False)
    customer_language: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_summary: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    open_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    missing_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    advisory_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    decision_queue_item_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("decision_queue_items.id"), index=True
    )
