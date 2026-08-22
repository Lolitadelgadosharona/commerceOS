from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


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
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)


@event.listens_for(DemandSignalEvidence, "before_update")
@event.listens_for(DemandSignalEvidence, "before_delete")
def _protect_demand_evidence(*_: object) -> None:
    raise ValueError("Demand signal evidence is append-only.")
