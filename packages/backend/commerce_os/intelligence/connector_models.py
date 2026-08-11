from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class MarketConnectorDefinition(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_connector_definitions"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    platform: Mapped[str] = mapped_column(String(80), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    configuration_schema: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MarketDataRecord(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_data_records"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_connector_definitions.id"), nullable=False, index=True
    )
    external_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_platform: Mapped[str | None] = mapped_column(String(30))
    external_id: Mapped[str | None] = mapped_column(String(120), index=True)
    subreddit: Mapped[str | None] = mapped_column(String(120))
    title: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(Text)
    author_reference: Mapped[str | None] = mapped_column(String(120))
    engagement_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NormalizedMarketItem(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "normalized_market_items"
    __table_args__ = (CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_record_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(150), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_language: Mapped[str] = mapped_column(Text, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class MarketIngestionJob(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "market_ingestion_jobs"
    __table_args__ = (CheckConstraint("record_count >= 0", name="record_count_nonnegative"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_connector_definitions.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_platform: Mapped[str | None] = mapped_column(String(30))


class RedditConnector(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "reddit_connectors"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    connector_definition_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_connector_definitions.id"), nullable=False, unique=True
    )
    subreddit_scope: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    keyword_scope: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    time_window: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class CustomerPainCandidate(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_pain_candidates"
    __table_args__ = (CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_record_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pain_category: Mapped[str] = mapped_column(String(30), nullable=False)
    customer_language: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class PainEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "pain_evidence"
    __table_args__ = (
        CheckConstraint("evidence_strength BETWEEN 0 AND 1", name="evidence_strength_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    pain_candidate_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("customer_pain_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_record_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("market_data_records.id", ondelete="CASCADE"), nullable=False
    )
    evidence_strength: Mapped[float] = mapped_column(Float, nullable=False)
