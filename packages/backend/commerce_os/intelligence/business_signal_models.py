from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class BusinessDemandSignal(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "business_demand_signals"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="business_demand_conf_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    source_domain: Mapped[str] = mapped_column(String(40), nullable=False)
    industry: Mapped[str] = mapped_column(String(160), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    source_research_result_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_business_research_results.id"), index=True
    )
