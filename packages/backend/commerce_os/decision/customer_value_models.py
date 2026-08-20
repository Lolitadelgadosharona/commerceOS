from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class CustomerValueAssessment(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "customer_value_assessments"
    __table_args__ = (
        CheckConstraint("revenue_indicator BETWEEN 0 AND 100", name="revenue_range"),
        CheckConstraint("margin_indicator BETWEEN 0 AND 100", name="margin_range"),
        CheckConstraint("repeat_probability BETWEEN 0 AND 1", name="repeat_range"),
        CheckConstraint("strategic_potential BETWEEN 0 AND 100", name="strategic_range"),
        CheckConstraint("risk_indicator BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("contribution_potential BETWEEN 0 AND 100", name="contribution_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revenue_indicator: Mapped[float] = mapped_column(nullable=False)
    margin_indicator: Mapped[float] = mapped_column(nullable=False)
    repeat_probability: Mapped[float] = mapped_column(nullable=False)
    strategic_potential: Mapped[float] = mapped_column(nullable=False)
    risk_indicator: Mapped[float] = mapped_column(nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    formula_version: Mapped[str] = mapped_column(String(50), nullable=False)
    contribution_potential: Mapped[float] = mapped_column(Float, nullable=False)
    risk_indicators: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
