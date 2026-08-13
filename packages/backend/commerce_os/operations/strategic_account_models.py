from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class StrategicAccountProfile(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "strategic_account_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", "customer_id"),
        CheckConstraint("relationship_strength BETWEEN 0 AND 100", name="relationship_range"),
        CheckConstraint("commercial_potential BETWEEN 0 AND 100", name="commercial_range"),
        CheckConstraint("expansion_potential BETWEEN 0 AND 100", name="expansion_range"),
        CheckConstraint("replenishment_potential BETWEEN 0 AND 100", name="replenishment_range"),
        CheckConstraint(
            "account_status IN ('candidate','active','watch','dormant','closed')",
            name="status_values",
        ),
        CheckConstraint(
            "strategic_tier IN ('standard','growth','strategic','key')", name="tier_values"
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    account_status: Mapped[str] = mapped_column(String(30))
    relationship_stage: Mapped[str] = mapped_column(String(50))
    strategic_tier: Mapped[str] = mapped_column(String(30))
    relationship_strength: Mapped[float]
    commercial_potential: Mapped[float]
    expansion_potential: Mapped[float]
    replenishment_potential: Mapped[float]
    risk_level: Mapped[str] = mapped_column(String(30))
    last_meaningful_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountStakeholder(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "account_stakeholders"
    __table_args__ = (
        UniqueConstraint("organization_id", "strategic_account_id", "contact_reference"),
        CheckConstraint("decision_influence BETWEEN 0 AND 100", name="influence_range"),
        CheckConstraint("relationship_strength BETWEEN 0 AND 100", name="relationship_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    strategic_account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("strategic_account_profiles.id", ondelete="CASCADE"), index=True
    )
    contact_reference: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(100))
    decision_influence: Mapped[float]
    decision_maker: Mapped[bool]
    relationship_strength: Mapped[float]
    evidence_reference: Mapped[str | None] = mapped_column(Text)
