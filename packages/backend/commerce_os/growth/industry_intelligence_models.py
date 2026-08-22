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


class IndustryGrowthProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "industry_growth_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", "industry_key"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="industry_profile_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    industry_key: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    vertical: Mapped[str] = mapped_column(String(120), nullable=False)
    scope_notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    confidence: Mapped[float] = mapped_column(nullable=False)


class IndustryGrowthEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "industry_growth_evidence"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="industry_evidence_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    industry_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id", ondelete="CASCADE"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IndustryGrowthPattern(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "industry_growth_patterns"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="industry_pattern_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    industry_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id", ondelete="CASCADE"), index=True
    )
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")


class GrowthGEOAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_geo_assessments"
    __table_args__ = (
        UniqueConstraint("prospect_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_geo_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    industry_profile_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id"), index=True
    )
    website_signals: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    social_signals: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    review_signals: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    visibility_gaps: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)


class GrowthServiceRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "growth_service_recommendations"
    __table_args__ = (
        CheckConstraint(
            "confidence BETWEEN 0 AND 1", name="service_recommendation_confidence_range"
        ),
        CheckConstraint(
            "purchase_probability IS NULL OR purchase_probability BETWEEN 0 AND 1",
            name="service_purchase_probability_range",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    industry_profile_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id"), index=True
    )
    opportunity_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_opportunity_analyses.id"), index=True
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_problem: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_scope: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    purchase_probability: Mapped[float | None] = mapped_column()
    quick_win_potential: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")


class IndustryLearningSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "industry_learning_signals"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="industry_learning_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    industry_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")


@event.listens_for(IndustryGrowthEvidence, "before_update")
def _prevent_industry_evidence_update(*_: object) -> None:
    raise ValueError("Industry growth evidence is immutable.")
