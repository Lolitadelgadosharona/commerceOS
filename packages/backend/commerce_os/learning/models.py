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
from sqlalchemy import event as sqlalchemy_event
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class LearningObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "learning_observations"
    __table_args__ = (
        UniqueConstraint("organization_id", "source_type", "source_record_id", "observation_type"),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"), index=True)
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    source_domain: Mapped[str] = mapped_column(String(30), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_record_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    observation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    observation_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)


@sqlalchemy_event.listens_for(LearningObservation, "before_update")
@sqlalchemy_event.listens_for(LearningObservation, "before_delete")
def _protect_observation(_mapper: object, _connection: object, _target: object) -> None:
    raise ValueError("Learning observations are append-only.")


class RootCauseHypothesis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "root_cause_hypotheses"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"), index=True)
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), index=True)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(Uuid)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)


class RootCauseEvidenceLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "root_cause_evidence_links"
    __table_args__ = (UniqueConstraint("hypothesis_id", "observation_id"),)

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    hypothesis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("root_cause_hypotheses.id", ondelete="CASCADE"), index=True
    )
    observation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("learning_observations.id"), index=True
    )
    evidence_role: Mapped[str] = mapped_column(String(20), nullable=False)


class LearningConclusion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "learning_conclusions"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("evidence_coverage BETWEEN 0 AND 1", name="coverage_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    hypothesis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("root_cause_hypotheses.id"), index=True
    )
    conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_observation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    contradicting_observation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ImprovementRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "improvement_recommendations"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    conclusion_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("learning_conclusions.id"), index=True
    )
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(Uuid)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    decision_queue_item_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("decision_queue_items.id")
    )


class RecommendationPriorityAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "recommendation_priority_assessments"
    __table_args__ = (
        UniqueConstraint("recommendation_id"),
        CheckConstraint("calculated_score BETWEEN 0 AND 100", name="score_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    recommendation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("improvement_recommendations.id", ondelete="CASCADE"), index=True
    )
    formula_version: Mapped[str] = mapped_column(String(80), nullable=False)
    supplied_inputs: Mapped[dict[str, float | None]] = mapped_column(JSON, nullable=False)
    missing_inputs: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    calculated_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_components: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
