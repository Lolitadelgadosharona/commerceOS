from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
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


class ListingStrategyStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ListingStrategy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_strategies"
    __table_args__ = (UniqueConstraint("product_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_customer: Mapped[str] = mapped_column(Text, nullable=False)
    value_proposition: Mapped[str] = mapped_column(Text, nullable=False)
    positioning: Mapped[str] = mapped_column(Text, nullable=False)
    differentiation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ListingStrategyStatus] = mapped_column(String(30), nullable=False)


class CustomerQuestion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_questions"
    __table_args__ = (
        UniqueConstraint("product_id", "question", "source_reference"),
        CheckConstraint("importance_score BETWEEN 0 AND 100", name="importance_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False)


class ProductDiscoveryKnowledge(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_discovery_knowledge"
    __table_args__ = (
        UniqueConstraint("product_id", "entity_type", "entity_name", "relationship"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    relationship: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class ContentBrief(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "content_briefs"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    headline_direction: Mapped[str] = mapped_column(Text, nullable=False)
    key_benefits: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    proof_points: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    objections: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    trust_elements: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class ListingEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_evidence"
    __table_args__ = (
        UniqueConstraint("product_id", "evidence_type", "source_reference"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
