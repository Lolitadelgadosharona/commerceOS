from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

PipelineStage = Literal[
    "new_prospect",
    "qualified",
    "gift_ready",
    "approved",
    "sent",
    "reply_received",
    "conversation",
    "proposal",
    "paid",
    "delivery",
    "subscription",
]


class RevenuePipelineCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    notes: str = Field(default="", max_length=20_000)


class RevenuePipelineTransition(BaseModel):
    stage: PipelineStage
    notes: str = Field(default="", max_length=20_000)


class RevenuePipelineRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    stage: str
    owner_id: UUID
    stage_entered_at: datetime
    notes: str


class RevenueOfferCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    recommendation_id: UUID | None = None
    offer_name: str = Field(min_length=1, max_length=200)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    scope: str = Field(min_length=1, max_length=20_000)


class RevenueOfferTransition(BaseModel):
    status: Literal["presented", "accepted", "rejected"]
    customer_response: str = Field(min_length=1, max_length=20_000)


class RevenueOfferRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    recommendation_id: UUID | None
    offer_name: str
    price: Decimal | None
    currency: str | None
    scope: str
    customer_response: str | None
    status: str


class PaymentReadinessCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    offer_tracking_id: UUID
    payment_provider_reference: str | None = Field(default=None, max_length=500)
    payment_link: str | None = Field(default=None, max_length=1000)
    invoice_reference: str | None = Field(default=None, max_length=500)


class PaymentStatusTransition(BaseModel):
    payment_status: Literal["link_ready", "invoiced", "paid_observed", "failed", "cancelled"]
    revenue_observation_id: UUID | None = None


class PaymentReadinessRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    offer_tracking_id: UUID
    payment_provider_reference: str | None
    payment_link: str | None
    invoice_reference: str | None
    payment_status: str
    revenue_observation_id: UUID | None


class CustomerLifecycleEventCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    lifecycle_type: Literal[
        "first_purchase", "delivery", "feedback", "expansion_opportunity", "subscription_possible"
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    occurred_at: datetime
    notes: str = Field(default="", max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerLifecycleEventRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    lifecycle_type: str
    source_reference: str
    occurred_at: datetime
    notes: str
    event_metadata: dict[str, Any]
    recorded_by: UUID


class RevenueCommandCenter(BaseModel):
    organization_id: UUID
    dashboard_date: date
    todays_opportunities: int
    priority_prospects: int
    growth_gifts_ready: int
    pending_approvals: int
    sent_outreach: int
    customer_replies: int
    pipeline_by_stage: dict[str, int]
    paid_customers: int
