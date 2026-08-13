from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class MarketplaceReviewEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "marketplace_review_evidence"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "marketplace", "source_identity", name="uq_marketplace_review_source"
        ),
        UniqueConstraint("organization_id", "evidence_hash", name="uq_marketplace_review_hash"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="rating_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    connector_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_connector_definitions.id"), nullable=False, index=True
    )
    ingestion_job_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("market_ingestion_jobs.id"), index=True
    )
    source_record_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_records.id"), nullable=False, unique=True
    )
    marketplace: Mapped[str] = mapped_column(String(30), nullable=False)
    source_identity: Mapped[str] = mapped_column(String(500), nullable=False)
    product_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_text_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    verified_indicator: Mapped[bool | None] = mapped_column(nullable=True)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class NormalizedMarketplaceReview(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "normalized_marketplace_reviews"
    __table_args__ = (
        UniqueConstraint("review_evidence_id"),
        CheckConstraint("evidence_confidence BETWEEN 0 AND 1", name="evidence_confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    review_evidence_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("marketplace_review_evidence.id"), nullable=False, index=True
    )
    sentiment_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    topic_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    customer_language: Mapped[str] = mapped_column(Text, nullable=False)
    product_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_confidence: Mapped[float] = mapped_column(Float, nullable=False)


class MarketplaceEvidenceLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "marketplace_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "review_evidence_id", "target_type", "target_id", name="uq_marketplace_evidence_target"
        ),
        CheckConstraint("evidence_strength BETWEEN 0 AND 1", name="evidence_strength_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    review_evidence_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("marketplace_review_evidence.id"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    evidence_strength: Mapped[float] = mapped_column(Float, nullable=False)


class CompetitiveMarketplaceObservation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "competitive_marketplace_observations"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    review_evidence_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("marketplace_review_evidence.id"), nullable=False, index=True
    )
    competitor_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    product_observations: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    customer_preference_signals: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    recurring_complaints: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


@event.listens_for(MarketplaceReviewEvidence, "before_update")
@event.listens_for(MarketplaceReviewEvidence, "before_delete")
def prevent_marketplace_evidence_mutation(*_: object) -> None:
    raise ValueError("Marketplace review evidence is immutable.")
