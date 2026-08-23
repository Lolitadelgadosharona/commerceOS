from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from commerce_os.shared.schemas import ReadModel


class DailyRevenueRunCreate(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    run_date: date
    industry: str = Field(min_length=1, max_length=120)
    target_geography: str = Field(min_length=1, max_length=240)


class DailyRunProspectAdd(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    priority_rank: int = Field(ge=1)
    priority_score: float | None = Field(default=None, ge=0, le=100)
    evidence_reference: str = Field(min_length=1, max_length=500)


class DailyRevenueRunTransition(BaseModel):
    review_status: Literal["ready_for_review", "approved", "rejected", "completed"]


class DailyRevenueRunRead(ReadModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    run_date: date
    industry: str
    target_geography: str
    generated_prospects: int
    review_status: str
    created_by: UUID
    reviewed_by: UUID | None


class DailyRunProspectRead(ReadModel):
    organization_id: UUID
    daily_revenue_run_id: UUID
    prospect_id: UUID
    priority_rank: int
    priority_score: float | None
    evidence_reference: str


class FounderActionCreate(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID | None = None
    prospect_id: UUID | None = None
    action_type: Literal[
        "prospect_review", "gift_approval", "reply_analysis", "offer_decision", "delivery_task"
    ]
    source_type: Literal[
        "daily_workspace", "growth_gift", "customer_feedback", "revenue_offer", "delivery_item"
    ]
    source_reference_id: UUID
    title: str = Field(min_length=1, max_length=240)
    priority: int = Field(ge=1, le=100)


class FounderActionDecision(BaseModel):
    action: Literal["approve", "reject", "assign", "complete"]
    assigned_to: UUID | None = None
    notes: str = Field(default="", max_length=20_000)

    @model_validator(mode="after")
    def assignment_required(self) -> Self:
        if self.action == "assign" and self.assigned_to is None:
            raise ValueError("Assign action requires assigned_to.")
        if self.action != "assign" and self.assigned_to is not None:
            raise ValueError("assigned_to is only valid for assign action.")
        return self


class FounderActionRead(ReadModel):
    organization_id: UUID
    revenue_experiment_id: UUID | None
    prospect_id: UUID | None
    action_type: str
    source_type: str
    source_reference_id: UUID
    title: str
    priority: int
    status: str
    assigned_to: UUID | None
    completed_at: datetime | None
    decision_notes: str


class GrowthConnectorCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=160)
    provider: str = Field(min_length=1, max_length=120)
    data_type: Literal["website", "google_business", "social_profile", "email"]
    collection_mode: Literal["human_review", "controlled_import", "controlled_connector"]
    credential_reference: str | None = Field(default=None, max_length=500)
    configuration: dict[str, Any] = Field(default_factory=dict)
    policy_reference: str = Field(min_length=1, max_length=500)


class GrowthConnectorTransition(BaseModel):
    status: Literal["configured", "ready", "disabled"]


class GrowthConnectorRead(ReadModel):
    organization_id: UUID
    name: str
    provider: str
    data_type: str
    collection_mode: str
    credential_reference: str | None
    configuration_metadata: dict[str, Any]
    policy_reference: str
    status: str


class CustomerDeliveryCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    offer_tracking_id: UUID


class CustomerDeliveryTransition(BaseModel):
    status: Literal["in_progress", "blocked", "completed", "cancelled"]
    customer_feedback_reference: str | None = Field(default=None, max_length=500)


class CustomerDeliveryRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    offer_tracking_id: UUID
    status: str
    owner_id: UUID
    started_at: datetime | None
    completed_at: datetime | None
    customer_feedback_reference: str | None


class DeliveryItemCreate(BaseModel):
    organization_id: UUID
    item_type: Literal["checklist", "milestone", "customer_feedback", "expansion_opportunity"]
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1, max_length=20_000)
    sequence: int = Field(ge=1)
    due_at: datetime | None = None
    evidence_reference: str | None = Field(default=None, max_length=500)


class DeliveryItemTransition(BaseModel):
    status: Literal["in_progress", "blocked", "completed", "cancelled"]
    evidence_reference: str | None = Field(default=None, max_length=500)


class DeliveryItemRead(ReadModel):
    organization_id: UUID
    delivery_id: UUID
    item_type: str
    title: str
    description: str
    sequence: int
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    evidence_reference: str | None


class LiveRevenueExperimentAnalytics(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    prospects_reviewed: int
    gifts_approved: int
    outreach_sent: int
    replies: int
    positive_replies: int
    offers: int
    paid_customers: int
    paid_revenue: Decimal
    revenue_currency: str | None
    lost_reasons: dict[str, int]
