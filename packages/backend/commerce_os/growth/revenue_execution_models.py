from datetime import date
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Date, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class DailyGrowthOpportunity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "daily_growth_opportunities"
    __table_args__ = (
        UniqueConstraint("organization_id", "queue_date", "prospect_id"),
        CheckConstraint(
            "opportunity_score IS NULL OR opportunity_score BETWEEN 0 AND 100",
            name="score_range",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), index=True)
    queue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    industry_profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("industry_growth_profiles.id"), index=True
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("growth_prospects.id"), index=True)
    evidence_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    growth_pain: Mapped[str] = mapped_column(Text, nullable=False)
    industry_pattern_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("industry_growth_patterns.id"), index=True
    )
    opportunity_score: Mapped[float | None] = mapped_column()
    service_recommendation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_service_recommendations.id"), index=True
    )
    growth_gift_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_gifts.id"), index=True
    )
    confidence: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="review")
