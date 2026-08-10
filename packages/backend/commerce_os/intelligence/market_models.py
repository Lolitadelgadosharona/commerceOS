from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class MarketDataSource(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_data_sources"
    __table_args__ = (
        UniqueConstraint("organization_id", "name"),
        CheckConstraint("reliability_score BETWEEN 0 AND 1", name="reliability_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    platform: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    access_method: Mapped[str] = mapped_column(String(40), nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class MarketSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signals"
    __table_args__ = (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_sources.id"), nullable=False, index=True
    )
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class MarketSignalEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signal_evidence"
    __table_args__ = (
        UniqueConstraint("signal_id", "evidence_type", "content_reference"),
        CheckConstraint("strength_score BETWEEN 0 AND 1", name="strength_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(60), nullable=False)
    content_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    strength_score: Mapped[float] = mapped_column(Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketSignalCluster(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signal_clusters"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("impact_score BETWEEN 0 AND 100", name="impact_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)


class MarketSignalClusterMembership(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signal_cluster_memberships"
    __table_args__ = (UniqueConstraint("cluster_id", "signal_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    cluster_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_signal_clusters.id", ondelete="CASCADE"), nullable=False
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_signals.id", ondelete="CASCADE"), nullable=False
    )


class MarketSignalOpportunityLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_signal_opportunity_links"
    __table_args__ = (UniqueConstraint("signal_id", "opportunity_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_signals.id", ondelete="CASCADE"), nullable=False
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_opportunities.id", ondelete="CASCADE"), nullable=False
    )
