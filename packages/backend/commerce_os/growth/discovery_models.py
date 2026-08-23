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
    adapter_key: Mapped[str] = mapped_column(String(120), nullable=False, default="manual")
    collection_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="human_review")


class DiscoveryAutomationPlan(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "discovery_automation_plans"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(160), nullable=False)
    geography: Mapped[str] = mapped_column(String(250), nullable=False)
    query_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    cadence: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)


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
    automation_plan_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("discovery_automation_plans.id"), index=True
    )
    query_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result_count: Mapped[int] = mapped_column(nullable=False, default=0)


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


class WebsiteEvidenceSnapshot(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "website_evidence_snapshots"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="website_evidence_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    business_name: Mapped[str] = mapped_column(String(250), nullable=False)
    location: Mapped[str | None] = mapped_column(String(250))
    services: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    website_structure: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    homepage_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    booking_flow_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    seo_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    geo_visibility_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


class BusinessProfileEvidenceSnapshot(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "business_profile_evidence_snapshots"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="bp_ev_conf"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    review_count: Mapped[int | None]
    rating: Mapped[float | None]
    location: Mapped[str | None] = mapped_column(String(250))
    business_category: Mapped[str | None] = mapped_column(String(160))
    customer_language: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


class InstagramEvidenceSnapshot(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "instagram_evidence_snapshots"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="instagram_evidence_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    profile_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    profile_information: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    posting_frequency: Mapped[str | None] = mapped_column(String(120))
    content_themes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    brand_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


class GoogleBusinessDiscoveryResult(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "google_business_discovery_results"
    __table_args__ = (
        UniqueConstraint("discovery_run_id", "external_reference"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="gb_result_conf"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    discovery_run_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_runs.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id"), index=True
    )
    external_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    business_name: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float | None]
    review_count: Mapped[int | None]
    website: Mapped[str | None] = mapped_column(String(500))
    public_profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


class ProspectMemoryEvent(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prospect_memory_events"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_memory_conf"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_candidates.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("prospect_discovery_sources.id"), index=True
    )
    change_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    previous_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


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
@event.listens_for(WebsiteEvidenceSnapshot, "before_update")
@event.listens_for(WebsiteEvidenceSnapshot, "before_delete")
@event.listens_for(BusinessProfileEvidenceSnapshot, "before_update")
@event.listens_for(BusinessProfileEvidenceSnapshot, "before_delete")
@event.listens_for(InstagramEvidenceSnapshot, "before_update")
@event.listens_for(InstagramEvidenceSnapshot, "before_delete")
@event.listens_for(GoogleBusinessDiscoveryResult, "before_update")
@event.listens_for(GoogleBusinessDiscoveryResult, "before_delete")
@event.listens_for(ProspectMemoryEvent, "before_update")
@event.listens_for(ProspectMemoryEvent, "before_delete")
def _protect_research_evidence(*_: object) -> None:
    raise ValueError("Prospect discovery evidence is immutable.")
