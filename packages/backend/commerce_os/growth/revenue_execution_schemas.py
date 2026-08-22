from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class DailyOpportunityCreate(BaseModel):
    organization_id: UUID
    queue_date: date
    industry_profile_id: UUID
    prospect_id: UUID
    evidence_references: list[UUID] = Field(min_length=1)
    growth_pain: str = Field(min_length=1, max_length=20_000)
    industry_pattern_id: UUID
    opportunity_score: float | None = Field(default=None, ge=0, le=100)
    service_recommendation_id: UUID
    growth_gift_id: UUID | None = None
    confidence: float = Field(ge=0, le=1)


class DailyOpportunityRead(ReadModel):
    organization_id: UUID
    queue_date: date
    industry_profile_id: UUID
    prospect_id: UUID
    evidence_references: list[str]
    growth_pain: str
    industry_pattern_id: UUID
    opportunity_score: float | None
    service_recommendation_id: UUID
    growth_gift_id: UUID | None
    confidence: float
    status: str


class GiftResponseTransition(BaseModel):
    status: str
    approval_request_id: UUID | None = None
    customer_response: str | None = Field(default=None, max_length=20_000)


class RevenueExecutionDashboard(BaseModel):
    organization_id: UUID
    prospects_discovered: int
    qualified_prospects: int
    growth_gifts_created: int
    outreach_drafts: int
    customer_replies: int
    positive_conversations: int
    customers_won: int
    revenue: Decimal
    mrr: Decimal | None
    ltv: Decimal | None
    currency: str | None
