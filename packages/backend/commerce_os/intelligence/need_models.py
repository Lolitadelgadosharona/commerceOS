from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CustomerNeed(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_needs"
    __table_args__ = (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class PainNeedMapping(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "pain_need_mappings"
    __table_args__ = (
        CheckConstraint("mapping_strength BETWEEN 0 AND 1", name="mapping_strength_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    pain_cluster_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_pain_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    need_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_needs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mapping_strength: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ProductSolutionHypothesis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_solution_hypotheses"
    __table_args__ = (
        CheckConstraint("fit_score BETWEEN 0 AND 100", name="fit_range"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    need_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_needs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_category: Mapped[str] = mapped_column(String(120), nullable=False)
    solution_description: Mapped[str] = mapped_column(Text, nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class CustomerBackedOpportunityAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_backed_opportunity_assessments"
    __table_args__ = tuple(
        CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
        for field, name in {
            "pain_strength": "pain_range",
            "solution_fit": "fit_range",
            "intent_score": "intent_range",
            "competition_score": "competition_range",
            "margin_score": "margin_range",
            "risk_score": "risk_range",
            "overall_score": "overall_range",
        }.items()
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    need_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_needs.id"), nullable=False, index=True
    )
    pain_strength: Mapped[float] = mapped_column(Float, nullable=False)
    solution_fit: Mapped[float] = mapped_column(Float, nullable=False)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    margin_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)
