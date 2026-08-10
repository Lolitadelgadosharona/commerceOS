from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ChannelStrategyStatus(StrEnum):
    DRAFT = "draft"
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ChannelStrategy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_strategies"
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creative_strategy_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("creative_strategies.id")
    )
    market: Mapped[str] = mapped_column(String(150), nullable=False)
    geography: Mapped[str] = mapped_column(String(150), nullable=False)
    audience: Mapped[str] = mapped_column(Text, nullable=False)
    business_model: Mapped[str] = mapped_column(String(10), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ChannelStrategyStatus] = mapped_column(String(30), nullable=False)


class ChannelCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_candidates"
    __table_args__ = (
        UniqueConstraint("strategy_id", "channel"),
        CheckConstraint("suitability_score BETWEEN 0 AND 100", name="suitability_range"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("channel_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    distribution_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    suitability_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)


class ChannelOpportunityScore(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_opportunity_scores"
    __table_args__ = (
        UniqueConstraint("candidate_id"),
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="overall_range"),
        CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("channel_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_customer_fit: Mapped[float | None] = mapped_column(Float)
    product_fit: Mapped[float | None] = mapped_column(Float)
    buying_intent: Mapped[float | None] = mapped_column(Float)
    visual_fit: Mapped[float | None] = mapped_column(Float)
    organic_potential: Mapped[float | None] = mapped_column(Float)
    search_discovery_potential: Mapped[float | None] = mapped_column(Float)
    content_cost: Mapped[float | None] = mapped_column(Float)
    competition: Mapped[float | None] = mapped_column(Float)
    expected_acquisition_cost: Mapped[float | None] = mapped_column(Float)
    historical_performance_confidence: Mapped[float | None] = mapped_column(Float)
    conversion_path_fit: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(30), nullable=False)


class ConversionPath(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversion_paths"
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("channel_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    business_model: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class ConversionPathStep(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "conversion_path_steps"
    __table_args__ = (UniqueConstraint("path_id", "sequence"),)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    path_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversion_paths.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(80))
    responsible_domain: Mapped[str] = mapped_column(String(30), nullable=False)
    human_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ChannelMeasurementPlan(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_measurement_plans"
    __table_args__ = (UniqueConstraint("strategy_id"),)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("channel_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metrics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)


class ChannelDecisionEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "channel_decision_evidence"
    __table_args__ = (
        UniqueConstraint("strategy_id", "evidence_type", "source_reference"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("channel_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
