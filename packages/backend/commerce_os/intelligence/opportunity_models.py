from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class OpportunityStatus(StrEnum):
    OBSERVED = "observed"
    EVALUATING = "evaluating"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class TriggerType(StrEnum):
    WEATHER_EVENT = "weather_event"
    SEASONAL_EVENT = "seasonal_event"
    CULTURAL_EVENT = "cultural_event"
    CUSTOMER_PAIN = "customer_pain"
    TREND_SHIFT = "trend_shift"
    REGULATORY_CHANGE = "regulatory_change"
    SUPPLY_CHANGE = "supply_change"


class OpportunityEvidenceSource(StrEnum):
    CUSTOMER_SIGNAL = "customer_signal"
    SEARCH_TREND = "search_trend"
    NEWS = "news"
    REVIEW = "review"
    SOCIAL = "social"
    MARKET_REPORT = "market_report"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CandidateStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    ARCHIVED = "archived"
    PROPOSED = "proposed"
    REVIEWING = "reviewing"
    SELECTED = "selected"
    REJECTED = "rejected"


class OpportunityRiskType(StrEnum):
    TRADEMARK = "trademark"
    BRAND = "brand"
    POLICY = "policy"
    DISPUTE = "dispute"
    PAYMENT = "payment"


class OpportunityRiskStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


class MarketOpportunity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_opportunities"
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"),
        Index("ix_market_opportunities_status", "organization_id", "status", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    market: Mapped[str] = mapped_column(String(150), nullable=False)
    geography: Mapped[str] = mapped_column(String(150), nullable=False)
    trigger_type: Mapped[TriggerType] = mapped_column(String(50), nullable=False)
    timing_window: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[OpportunityStatus] = mapped_column(String(30), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class OpportunityEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_evidence"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "source_type", "source_reference"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[OpportunityEvidenceSource] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)


class ProductCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_candidates"
    __table_args__ = (
        CheckConstraint("estimated_margin >= 0 AND estimated_margin <= 1", name="margin_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    opportunity_candidate_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("opportunity_discovery_candidates.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_need: Mapped[str] = mapped_column(Text, nullable=False)
    target_customer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    product_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    value_proposition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_margin: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(String(30), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(String(30), nullable=False)


class ProductEvaluation(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_evaluations"
    __table_args__ = (
        UniqueConstraint("product_candidate_id"),
        CheckConstraint("demand_fit_score BETWEEN 0 AND 100", name="demand_fit_range"),
        CheckConstraint("problem_solution_fit BETWEEN 0 AND 100", name="solution_fit_range"),
        CheckConstraint("gross_margin_estimate BETWEEN 0 AND 1", name="gross_margin_range"),
        CheckConstraint("evaluation_score BETWEEN 0 AND 100", name="evaluation_score_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), index=True
    )
    demand_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    problem_solution_fit: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_price_range: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    estimated_cost_range: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    gross_margin_estimate: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_complexity: Mapped[str] = mapped_column(String(20), nullable=False)
    fulfillment_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    regulatory_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    dispute_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    evaluation_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(50), nullable=False)


class ProductCandidateEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "product_candidate_evidence"
    __table_args__ = (
        UniqueConstraint("product_candidate_id", "evidence_source", "source_reference"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    product_candidate_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("product_candidates.id", ondelete="CASCADE"), index=True
    )
    evidence_source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    relevance: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


@event.listens_for(ProductCandidateEvidence, "before_update")
@event.listens_for(ProductCandidateEvidence, "before_delete")
def _protect_product_candidate_evidence(*_: object) -> None:
    raise ValueError("Product candidate evidence is append-only.")


class OpportunityScore(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_scores"
    __table_args__ = (
        UniqueConstraint("opportunity_id"),
        CheckConstraint("demand_score >= 0 AND demand_score <= 100", name="demand_range"),
        CheckConstraint("pain_score >= 0 AND pain_score <= 100", name="pain_range"),
        CheckConstraint("trend_score >= 0 AND trend_score <= 100", name="trend_range"),
        CheckConstraint("margin_score >= 0 AND margin_score <= 100", name="margin_range"),
        CheckConstraint(
            "competition_score >= 0 AND competition_score <= 100", name="competition_range"
        ),
        CheckConstraint("ip_risk_score >= 0 AND ip_risk_score <= 100", name="ip_risk_range"),
        CheckConstraint(
            "dispute_risk_score >= 0 AND dispute_risk_score <= 100", name="dispute_risk_range"
        ),
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="overall_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    pain_score: Mapped[float] = mapped_column(Float, nullable=False)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)
    margin_score: Mapped[float] = mapped_column(Float, nullable=False)
    competition_score: Mapped[float] = mapped_column(Float, nullable=False)
    ip_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    dispute_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(30), nullable=False)


class OpportunityRisk(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "opportunity_risks"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_type: Mapped[OpportunityRiskType] = mapped_column(String(30), nullable=False)
    severity: Mapped[RiskLevel] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OpportunityRiskStatus] = mapped_column(String(30), nullable=False)
