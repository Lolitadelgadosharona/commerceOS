from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class MarketSignalAnalysis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signal_analyses"
    __table_args__ = (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_type: Mapped[str] = mapped_column(String(60), nullable=False)
    market_impact: Mapped[str] = mapped_column(Text, nullable=False)
    timing_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    customer_relevance: Mapped[str] = mapped_column(Text, nullable=False)
    commercial_relevance: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class OpportunityAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_assessments"
    __table_args__ = (
        CheckConstraint("demand_score BETWEEN 0 AND 100", name="demand_range"),
        CheckConstraint("timing_score BETWEEN 0 AND 100", name="timing_range"),
        CheckConstraint("evidence_score BETWEEN 0 AND 100", name="evidence_range"),
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint("commercial_score BETWEEN 0 AND 100", name="commercial_range"),
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="overall_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    market_opportunity_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("market_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    timing_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    commercial_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)


class OpportunityReport(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_reports"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_actions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_queue_item_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("decision_queue_items.id")
    )
