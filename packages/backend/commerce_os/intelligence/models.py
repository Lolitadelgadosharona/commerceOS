from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class SignalSourceType(StrEnum):
    REDDIT = "reddit"
    AMAZON_REVIEW = "amazon_review"
    ETSY_REVIEW = "etsy_review"
    SHOPIFY = "shopify"
    EMAIL = "email"
    SOCIAL = "social"
    SUPPORT = "support"
    B2B_CONVERSATION = "b2b_conversation"


class SignalType(StrEnum):
    QUALITY_CONCERN = "quality_concern"
    DELIVERY_DELAY = "delivery_delay"
    PRICE_OBJECTION = "price_objection"
    TRUST_CONCERN = "trust_concern"
    FEATURE_REQUEST = "feature_request"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(StrEnum):
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    UNKNOWN = "unknown"


class InsightStatus(StrEnum):
    NEW = "new"
    VALIDATED = "validated"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class SignalSource(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "signal_sources"
    __table_args__ = (UniqueConstraint("organization_id", "source_type", "name"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_type: Mapped[SignalSourceType] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class CustomerSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_signals"
    __table_args__ = (
        UniqueConstraint("organization_id", "source_type", "source_reference"),
        Index("ix_customer_signals_type_created", "organization_id", "signal_type", "created_at"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    signal_source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("signal_sources.id"), nullable=False, index=True
    )
    source_type: Mapped[SignalSourceType] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    customer_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("customers.id"), index=True)
    signal_type: Mapped[SignalType] = mapped_column(String(50), nullable=False)
    content_reference: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[Sentiment] = mapped_column(String(30), nullable=False)
    severity: Mapped[Severity] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class CustomerVoiceCluster(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_voice_clusters"
    __table_args__ = (CheckConstraint("signal_count >= 0", name="signal_count_nonnegative"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    signal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    severity: Mapped[Severity] = mapped_column(String(30), nullable=False)
    trend_direction: Mapped[TrendDirection] = mapped_column(String(30), nullable=False)


class SignalClusterMembership(IdMixin, TimestampMixin, Base):
    __tablename__ = "signal_cluster_memberships"
    __table_args__ = (UniqueConstraint("cluster_id", "signal_id"),)

    cluster_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_voice_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_signals.id", ondelete="CASCADE"), nullable=False, index=True
    )


class CustomerInsight(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_insights"
    __table_args__ = (CheckConstraint("evidence_count >= 1", name="evidence_count_positive"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    cluster_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("customer_voice_clusters.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    impact_level: Mapped[Severity] = mapped_column(String(30), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InsightStatus] = mapped_column(String(30), nullable=False)


class InsightEvidence(IdMixin, TimestampMixin, Base):
    __tablename__ = "insight_evidence"
    __table_args__ = (UniqueConstraint("insight_id", "signal_id"),)

    insight_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_insights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customer_signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
