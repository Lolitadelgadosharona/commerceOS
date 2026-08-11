from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProductPositioning(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_positioning"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_customer: Mapped[str] = mapped_column(Text, nullable=False)
    customer_problem: Mapped[str] = mapped_column(Text, nullable=False)
    primary_benefit: Mapped[str] = mapped_column(Text, nullable=False)
    differentiation: Mapped[str] = mapped_column(Text, nullable=False)
    positioning_statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class OfferStrategy(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "offer_strategies"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pricing_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    bundle_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    guarantee_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    bonus_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    urgency_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class ProductObjectionMap(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_objection_maps"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objection_type: Mapped[str] = mapped_column(String(80), nullable=False)
    customer_language: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_response: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)


class LaunchPreparationPackage(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "launch_preparation_packages"
    __table_args__ = (CheckConstraint("launch_score BETWEEN 0 AND 100", name="score_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    positioning_status: Mapped[str] = mapped_column(String(20), nullable=False)
    offer_status: Mapped[str] = mapped_column(String(20), nullable=False)
    objection_status: Mapped[str] = mapped_column(String(20), nullable=False)
    creative_readiness: Mapped[str] = mapped_column(String(20), nullable=False)
    listing_readiness: Mapped[str] = mapped_column(String(20), nullable=False)
    launch_score: Mapped[float] = mapped_column(Float, nullable=False)
