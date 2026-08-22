from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class RevenueExperimentCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=20_000)
    target_segment: str = Field(min_length=1, max_length=20_000)
    offer_type: str = Field(min_length=1, max_length=120)
    message_strategy: str = Field(min_length=1, max_length=20_000)
    industry_profile_id: UUID | None = None
    segment: str = Field(default="", max_length=200)
    target_count: int = Field(default=0, ge=0)
    start_date: date | None = None
    success_metrics: dict[str, float] = Field(default_factory=dict)


class RevenueExperimentTransition(BaseModel):
    status: Literal["active", "paused", "completed", "archived"]


class RevenueExperimentRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    target_segment: str
    offer_type: str
    message_strategy: str
    status: str
    created_by: UUID
    industry_profile_id: UUID | None
    segment: str
    target_count: int
    start_date: date | None
    success_metrics: dict[str, float]


class OfferExperimentCreate(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    offer_type: Literal[
        "growth_visibility_audit",
        "geo_optimization",
        "website_growth_fix",
        "ai_content_growth",
        "other",
    ]
    prospect_segment: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1, max_length=20_000)


class OfferExperimentRead(ReadModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    offer_type: str
    prospect_segment: str
    hypothesis: str
    status: str


class OfferOutcomeCreate(BaseModel):
    organization_id: UUID
    offer_experiment_id: UUID
    prospect_id: UUID
    outreach_sent: bool = False
    replied: bool = False
    positive_reply: bool = False
    converted: bool = False
    revenue_observation_id: UUID | None = None


class OfferOutcomeRead(ReadModel, OfferOutcomeCreate):
    pass


class FeedbackSignalCreate(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    offer_experiment_id: UUID | None = None
    source_type: Literal["reply", "objection", "question", "buying_reason", "rejection"]
    source_reference: str = Field(min_length=1, max_length=500)
    objection_category: str | None = Field(default=None, max_length=80)
    frequency: int = Field(default=1, ge=1)
    industry: str = Field(min_length=1, max_length=120)
    recommended_response: str = Field(min_length=1, max_length=20_000)
    learning_signal: str = Field(min_length=1, max_length=20_000)
    industry_learning_signal_id: UUID | None = None


class FeedbackSignalRead(ReadModel, FeedbackSignalCreate):
    pass


class FunnelMetric(BaseModel):
    name: str
    count: int
    conversion_rate: float | None


class OfferMetric(BaseModel):
    offer_experiment_id: UUID
    offer_type: str
    assigned: int
    response_rate: float | None
    conversion_rate: float | None
    revenue: Decimal
    currency: str | None


class RevenueExperimentDashboard(BaseModel):
    organization_id: UUID
    experiment_id: UUID
    funnel: list[FunnelMetric]
    offers: list[OfferMetric]
    revenue: Decimal
    currency: str | None
    estimated_ai_cost: Decimal
    ai_cost_currency: str | None


class ProspectAssignmentCreate(BaseModel):
    organization_id: UUID
    experiment_id: UUID
    prospect_id: UUID
    assigned_offer: str = Field(min_length=1, max_length=20_000)
    assigned_message: str = Field(min_length=1, max_length=20_000)


class ProspectAssignmentRead(ReadModel):
    organization_id: UUID
    experiment_id: UUID
    prospect_id: UUID
    assigned_offer: str
    assigned_message: str
    result_status: str


class OutreachEventCreate(BaseModel):
    organization_id: UUID
    prospect_experiment_link_id: UUID
    outreach_draft_id: UUID | None = None
    event_type: Literal[
        "draft_created",
        "approved",
        "sent_manually",
        "reply_received",
        "follow_up_needed",
        "converted",
    ]
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutreachEventRead(ReadModel):
    organization_id: UUID
    prospect_experiment_link_id: UUID
    outreach_draft_id: UUID | None
    event_type: str
    occurred_at: datetime
    recorded_by: UUID
    event_metadata: dict[str, Any]


class ProspectPromotionCreate(BaseModel):
    organization_id: UUID
    email: str | None = Field(default=None, max_length=320)
    social_links: dict[str, str] = Field(default_factory=dict)
