from datetime import datetime
from typing import Any
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


class ProspectDiscoverySource(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_discovery_sources"
    __table_args__ = (UniqueConstraint("organization_id", "source_name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    capability: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


class ProspectDiscoveryRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_discovery_runs"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    target_industry: Mapped[str] = mapped_column(String(160), nullable=False)
    target_location: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class ProspectCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_candidates"
    __table_args__ = (
        UniqueConstraint("organization_id", "duplicate_key"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_candidate_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    discovery_run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_runs.id"), index=True
    )
    business_name: Mapped[str] = mapped_column(String(250), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(160), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    duplicate_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class ProspectResearchEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_research_evidence"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_research_ev_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GrowthBusinessResearchRun(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_business_research_runs"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    capability_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_model_capabilities.id"), index=True
    )
    prompt_version_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("prompt_versions.id"), index=True
    )
    ai_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_requests.id"), index=True
    )
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)


class GrowthBusinessResearchResult(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_business_research_results"
    __table_args__ = (
        UniqueConstraint("research_run_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="result_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    research_run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_business_research_runs.id", ondelete="CASCADE"), index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    business_profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evidence_summary: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    potential_growth_issues: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class ProspectQualificationAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_qualification_assessments"
    __table_args__ = (UniqueConstraint("candidate_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[float | None]
    calculation_inputs: Mapped[dict[str, float | None]] = mapped_column(JSON, nullable=False)
    missing_inputs: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(80), nullable=False)


@event.listens_for(ProspectResearchEvidence, "before_update")
@event.listens_for(ProspectResearchEvidence, "before_delete")
def _protect_research_evidence(*_: object) -> None:
    raise ValueError("Prospect research evidence is immutable.")
