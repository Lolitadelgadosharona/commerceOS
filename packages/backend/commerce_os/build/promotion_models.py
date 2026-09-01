from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProductPromotion(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_promotions"
    __table_args__ = (
        UniqueConstraint("organization_id", "product_hypothesis_id"),
        UniqueConstraint("product_id"),
        UniqueConstraint("approval_request_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_hypothesis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_hypotheses.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id"), nullable=False, index=True
    )
    brand_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("brands.id"), nullable=False, index=True
    )
    approval_request_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("approval_requests.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("products.id"), nullable=True, index=True
    )
    requested_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    promoted_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")


class ProductTruthDraft(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_truth_drafts"
    __table_args__ = (UniqueConstraint("approval_request_id"), UniqueConstraint("truth_id"))

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    specifications: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    approved_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    restricted_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    usage_notes: Mapped[str] = mapped_column(Text, nullable=False)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    approval_request_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("approval_requests.id")
    )
    truth_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("product_truth.id"))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
