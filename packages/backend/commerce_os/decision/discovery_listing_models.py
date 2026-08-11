from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ListingBlueprint(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_blueprints"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    benefit_structure: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    feature_structure: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    faq_structure: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    trust_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    comparison_points: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class GeoKnowledgeAsset(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "geo_knowledge_assets"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_description: Mapped[str] = mapped_column(Text, nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    use_cases: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    customer_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    answer_structure: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)


class ListingQualityAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_quality_assessments"
    __table_args__ = tuple(
        CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
        for field, name in {
            "truth_score": "truth_range",
            "customer_language_score": "language_range",
            "geo_score": "geo_range",
            "trust_score": "trust_range",
            "conversion_score": "conversion_range",
            "overall_score": "overall_range",
        }.items()
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    truth_score: Mapped[float] = mapped_column(Float, nullable=False)
    customer_language_score: Mapped[float] = mapped_column(Float, nullable=False)
    geo_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)


class AIDiscoveryReadinessAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_discovery_readiness_assessments"
    __table_args__ = (CheckConstraint("coverage_score BETWEEN 0 AND 100", name="coverage_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
