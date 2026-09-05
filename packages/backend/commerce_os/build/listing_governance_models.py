from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ListingVersionStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"


class ListingVersion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_versions"
    __table_args__ = (
        UniqueConstraint("product_id", "listing_version"),
        CheckConstraint("listing_version > 0", name="listing_version_positive"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    product_truth_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("product_truth.id"), index=True)
    product_truth_version: Mapped[int] = mapped_column(Integer)
    listing_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[ListingVersionStatus] = mapped_column(
        String(30), default=ListingVersionStatus.DRAFT
    )
    title: Mapped[str] = mapped_column(String(250))
    subtitle: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    customer_problem: Mapped[str | None] = mapped_column(Text)
    solution: Mapped[str | None] = mapped_column(Text)
    features: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    specifications: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    use_cases: Mapped[list[str]] = mapped_column(JSON, default=list)
    whats_included: Mapped[list[str]] = mapped_column(JSON, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    care_usage: Mapped[str | None] = mapped_column(Text)
    shipping_facts: Mapped[str | None] = mapped_column(Text)
    return_facts: Mapped[str | None] = mapped_column(Text)
    risk_reversal: Mapped[str | None] = mapped_column(Text)
    seo_title: Mapped[str | None] = mapped_column(String(250))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    slug_suggestion: Mapped[str | None] = mapped_column(String(250))
    primary_topic: Mapped[str | None] = mapped_column(String(250))
    secondary_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    structured_attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    commercial_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    price_status: Mapped[str] = mapped_column(String(30), default="unknown")
    change_reason: Mapped[str] = mapped_column(Text)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id")
    )
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    approved_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ListingClaim(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_claims"
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    listing_version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("listing_versions.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(50))
    classification: Mapped[str] = mapped_column(String(30))
    support_status: Mapped[str] = mapped_column(String(30), default="unknown")
    risk_category: Mapped[str] = mapped_column(String(50), default="standard")
    review_status: Mapped[str] = mapped_column(String(30), default="pending")
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"))


class ListingClaimEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_claim_evidence"
    __table_args__ = (UniqueConstraint("claim_id", "source_type", "source_reference"),)
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    claim_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("listing_claims.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(50))
    source_reference: Mapped[str] = mapped_column(String(500))
    evidence_text: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(30))


class ListingFAQ(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "listing_faqs"
    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    listing_version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("listing_versions.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    answer_status: Mapped[str] = mapped_column(String(40), default="needs_review")
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
