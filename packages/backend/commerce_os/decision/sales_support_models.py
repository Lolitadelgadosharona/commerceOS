from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class RecommendationStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SalesIntelligenceProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "sales_intelligence_profiles"
    __table_args__ = (
        CheckConstraint(
            "repeat_probability IS NULL OR repeat_probability BETWEEN 0 AND 1",
            name="repeat_probability_range",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_threads.id"), nullable=False, index=True
    )
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("products.id"))
    intent: Mapped[str] = mapped_column(String(40), nullable=False)
    estimated_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    repeat_probability: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))


class SalesRecommendation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "sales_recommendations"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    sales_profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("sales_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_type: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(String(30), nullable=False)


class SupportCaseIntelligence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "support_case_intelligence"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("conversation_threads.id"), nullable=False, index=True
    )
    issue_category: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_impact: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_resolution: Mapped[str] = mapped_column(Text, nullable=False)


class CustomerRiskSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_risk_signals"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id"), nullable=False, index=True
    )
    risk_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(500), nullable=False)
