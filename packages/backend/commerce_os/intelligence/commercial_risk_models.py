from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class ProductRiskType(StrEnum):
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    SAFETY = "safety"
    REGULATORY = "regulatory"
    PAYMENT_DISPUTE = "payment_dispute"
    REFUND = "refund"
    SHIPPING = "shipping"
    QUALITY = "quality"
    CUSTOMER_EXPECTATION = "customer_expectation"


class ProductRiskStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


class CommercialRecommendation(StrEnum):
    GO = "go"
    TEST = "test"
    REVIEW = "review"
    REJECT = "reject"


class ProductRiskSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_risk_signals"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_type: Mapped[ProductRiskType] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ProductRiskStatus] = mapped_column(String(20), nullable=False)


class ProductRiskAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_risk_assessments"
    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)
    assessment_inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class CommercialViabilityAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "commercial_viability_assessments"
    __table_args__ = tuple(
        CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
        for field, name in {
            "opportunity_score": "opportunity_range",
            "risk_score": "risk_range",
            "adjusted_score": "adjusted_range",
        }.items()
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[CommercialRecommendation] = mapped_column(String(20), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
