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


class ProductStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Product(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "products"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    brand_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("brands.id"), nullable=False, index=True
    )
    status: Mapped[ProductStatus] = mapped_column(
        String(30), default=ProductStatus.DRAFT, nullable=False
    )


class ProductTruth(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_truth"
    __table_args__ = (
        UniqueConstraint("product_id", "version"),
        CheckConstraint("version > 0", name="version_positive"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    specifications: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    approved_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    restricted_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    usage_notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    approval_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), unique=True, nullable=False
    )


class KnowledgeItemType(StrEnum):
    FEATURE = "feature"
    FAQ = "faq"
    OBJECTION = "objection"
    LIMITATION = "limitation"
    USE_CASE = "use_case"
    CARE_INSTRUCTION = "care_instruction"


class KnowledgeApprovalStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProductKnowledgeItem(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_knowledge_items"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[KnowledgeItemType] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    approval_status: Mapped[KnowledgeApprovalStatus] = mapped_column(String(30), nullable=False)


class ProductClaimPolicy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_claim_policies"
    __table_args__ = (UniqueConstraint("brand_id", "claim_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    brand_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("brands.id"), nullable=False, index=True
    )
    claim_type: Mapped[str] = mapped_column(String(100), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
