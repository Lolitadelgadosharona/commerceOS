from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class DemandSignalSource(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "demand_signal_sources"
    __table_args__ = (UniqueConstraint("organization_id", "source_type"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(40), nullable=False)
    collection_method: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_origin: Mapped[str] = mapped_column(String(250), nullable=False)
    source_category: Mapped[str] = mapped_column(String(40), nullable=False)
    geographic_scope: Mapped[str | None] = mapped_column(String(200))
    time_window: Mapped[str | None] = mapped_column(String(120))
    trend_type: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class DemandSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "demand_signals"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("frequency > 0", name="positive_frequency"),
        CheckConstraint("evidence_count > 0", name="positive_evidence_count"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    source_domain: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    collection_method: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_origin: Mapped[str] = mapped_column(String(250), nullable=False)
    confidence_basis: Mapped[str] = mapped_column(Text, nullable=False)
    customer_segment: Mapped[str] = mapped_column(String(250), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    customer_language: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class DemandSignalEvidence(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "demand_signal_evidence"

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    demand_signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("demand_signals.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)


class PredictiveDemandMetadata(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "predictive_demand_metadata"
    __table_args__ = (
        UniqueConstraint("demand_signal_id"),
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    demand_signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("demand_signals.id", ondelete="CASCADE"), index=True
    )
    prediction_type: Mapped[str] = mapped_column(String(80), nullable=False)
    forecast_window: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    uncertainty_notes: Mapped[str] = mapped_column(Text, nullable=False)


class DemandThemeAnalysis(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "demand_theme_analyses"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("evidence_count > 0", name="positive_evidence_count"),
        CheckConstraint("signal_diversity > 0", name="positive_signal_diversity"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_diversity: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class DemandThemeSignalLink(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "demand_theme_signal_links"
    __table_args__ = (UniqueConstraint("theme_analysis_id", "demand_signal_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    theme_analysis_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("demand_theme_analyses.id", ondelete="CASCADE"), index=True
    )
    demand_signal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("demand_signals.id"), index=True
    )


@event.listens_for(DemandSignalEvidence, "before_update")
@event.listens_for(DemandSignalEvidence, "before_delete")
def _protect_demand_evidence(*_: object) -> None:
    raise ValueError("Demand signal evidence is append-only.")


@event.listens_for(PredictiveDemandMetadata, "before_update")
@event.listens_for(PredictiveDemandMetadata, "before_delete")
@event.listens_for(DemandThemeSignalLink, "before_update")
@event.listens_for(DemandThemeSignalLink, "before_delete")
def _protect_demand_analysis_evidence(*_: object) -> None:
    raise ValueError("Demand analysis evidence is append-only.")
