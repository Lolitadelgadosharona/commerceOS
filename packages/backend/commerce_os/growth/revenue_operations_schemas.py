from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from commerce_os.shared.schemas import ReadModel


class WorkspaceItemCreate(BaseModel):
    organization_id: UUID
    workspace_date: date
    revenue_experiment_id: UUID
    prospect_id: UUID
    daily_opportunity_id: UUID | None = None
    diagnosis_id: UUID | None = None
    growth_gift_id: UUID | None = None
    offer_recommendation_id: UUID | None = None
    priority: float | None = Field(default=None, ge=0, le=100)


class WorkspaceDecision(BaseModel):
    action: Literal["approve", "reject", "save_for_later"]
    review_notes: str = Field(min_length=1, max_length=20_000)


class WorkspaceItemRead(ReadModel):
    organization_id: UUID
    workspace_date: date
    revenue_experiment_id: UUID
    prospect_id: UUID
    daily_opportunity_id: UUID | None
    diagnosis_id: UUID | None
    growth_gift_id: UUID | None
    offer_recommendation_id: UUID | None
    priority: float | None
    status: str
    review_notes: str
    reviewed_by: UUID | None


class EmailWorkflowReferenceCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    outreach_draft_id: UUID | None = None
    email_account_reference: str = Field(min_length=1, max_length=500)
    draft_reference: str | None = Field(default=None, max_length=500)
    thread_reference: str | None = Field(default=None, max_length=500)
    inbound_reply_reference: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def at_least_one_message_reference(self) -> "EmailWorkflowReferenceCreate":
        if not any([self.draft_reference, self.thread_reference, self.inbound_reply_reference]):
            raise ValueError("At least one draft, thread, or inbound reply reference is required.")
        return self


class EmailWorkflowReferenceRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    outreach_draft_id: UUID | None
    email_account_reference: str
    draft_reference: str | None
    thread_reference: str | None
    inbound_reply_reference: str | None
    reference_metadata: dict[str, Any]
    recorded_by: UUID


class CustomerFeedbackCreate(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    prospect_id: UUID
    conversation_analysis_id: UUID | None = None
    customer_response: str = Field(min_length=1, max_length=20_000)
    interest_level: Literal["none", "low", "medium", "high", "customer"]
    objection_category: (
        Literal[
            "price", "timing", "trust", "existing_supplier", "no_need", "wrong_contact", "other"
        ]
        | None
    ) = None
    reason_lost: str | None = Field(default=None, max_length=20_000)
    reason_won: str | None = Field(default=None, max_length=20_000)
    learning_signal: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def mutually_exclusive_outcomes(self) -> "CustomerFeedbackCreate":
        if self.reason_lost and self.reason_won:
            raise ValueError("Feedback cannot record both a won and lost reason.")
        return self


class CustomerFeedbackDecision(BaseModel):
    status: Literal["reviewed", "approved", "rejected"]


class CustomerFeedbackRead(ReadModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    prospect_id: UUID
    conversation_analysis_id: UUID | None
    customer_response: str
    interest_level: str
    objection_category: str | None
    reason_lost: str | None
    reason_won: str | None
    learning_signal: str
    confidence: float
    status: str
    learning_observation_id: UUID | None
    reviewed_by: UUID | None


class RevenueExperimentOperationsDashboard(BaseModel):
    organization_id: UUID
    revenue_experiment_id: UUID
    prospects_discovered: int
    qualified_prospects: int
    gifts_created: int
    outreach_sent: int
    replies: int
    positive_conversations: int
    offers: int
    paid_customers: int
    revenue: Decimal
    revenue_currency: str | None
    estimated_ai_cost: Decimal
    ai_cost_currency: str | None
