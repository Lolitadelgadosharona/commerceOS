from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CustomerPainCluster(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_pain_clusters"
    __table_args__ = (
        CheckConstraint("severity_score BETWEEN 0 AND 100", name="severity_range"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    scoring_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class PainClusterMembership(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "pain_cluster_memberships"
    __table_args__ = (CheckConstraint("relevance_score BETWEEN 0 AND 1", name="relevance_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    cluster_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_pain_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pain_candidate_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_pain_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)


class CustomerLanguageInsight(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_language_insights"
    __table_args__ = (CheckConstraint("frequency >= 0", name="frequency_nonnegative"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    cluster_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_pain_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phrase: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    usage_type: Mapped[str] = mapped_column(String(20), nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)


class PurchaseIntentSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "purchase_intent_signals"
    __table_args__ = (
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("intent_score BETWEEN 0 AND 100", name="intent_score_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_record_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    intent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    intent_score: Mapped[float] = mapped_column(Float, nullable=False)
