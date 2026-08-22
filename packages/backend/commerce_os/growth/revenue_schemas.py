from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

ProspectStatus = Literal[
    "discovered", "researching", "qualified", "contacted", "replied", "customer", "disqualified"
]


class ProspectCreate(BaseModel):
    organization_id: UUID
    business_name: str = Field(min_length=1, max_length=250)
    website: str | None = Field(default=None, max_length=500)
    email: str | None = Field(default=None, max_length=320)
    social_links: dict[str, str] = Field(default_factory=dict)
    location: str | None = Field(default=None, max_length=250)
    industry: str = Field(min_length=1, max_length=120)
    business_type: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=120)


class ProspectTransition(BaseModel):
    status: ProspectStatus
    approval_request_id: UUID | None = None


class ProspectRead(ReadModel):
    organization_id: UUID
    business_name: str
    website: str | None
    email: str | None
    social_links: dict[str, str]
    location: str | None
    industry: str
    business_type: str
    source: str
    status: str


class ProspectEvidenceCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    evidence_type: str = Field(min_length=1, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    observation: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    collected_at: datetime


class ProspectEvidenceRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    evidence_type: str
    source_url: str | None
    observation: str
    confidence: float
    collected_at: datetime


class OpportunityAnalysisCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    opportunity_type: Literal[
        "homepage_fix",
        "booking_experience_fix",
        "google_profile_fix",
        "social_content_fix",
        "review_trust_fix",
        "other",
    ]
    problem_statement: str = Field(min_length=1, max_length=20_000)
    evidence_reference: list[UUID] = Field(min_length=1)
    customer_impact: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    recommended_offer: str = Field(min_length=1, max_length=20_000)
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    ai_request_id: UUID | None = None


class OpportunityAnalysisRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    opportunity_type: str
    problem_statement: str
    evidence_reference: list[str]
    customer_impact: str
    confidence: float
    recommended_offer: str
    risks: list[str]
    missing_information: list[str]
    ai_request_id: UUID | None


class GrowthGiftCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    opportunity_id: UUID
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=20_000)
    before_state: str = Field(min_length=1, max_length=20_000)
    after_state: str = Field(min_length=1, max_length=20_000)
    asset_reference: str | None = Field(default=None, max_length=500)


class StatusTransition(BaseModel):
    status: str
    approval_request_id: UUID | None = None


class GrowthGiftRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    opportunity_id: UUID
    title: str
    description: str
    before_state: str
    after_state: str
    asset_reference: str | None
    status: str
    approval_request_id: UUID | None


class OutreachDraftCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    growth_gift_id: UUID
    channel: Literal["email", "instagram_dm", "linkedin"]
    subject: str | None = Field(default=None, max_length=300)
    body: str = Field(min_length=1, max_length=20_000)
    tone: str = Field(min_length=1, max_length=80)
    evidence_used: list[UUID] = Field(min_length=1)
    ai_request_id: UUID


class OutreachDraftRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    growth_gift_id: UUID
    channel: str
    subject: str | None
    body: str
    tone: str
    evidence_used: list[str]
    status: str
    ai_request_id: UUID
    approval_request_id: UUID | None


class SalesAnalysisCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    conversation_reference: str = Field(min_length=1, max_length=500)
    intent: Literal[
        "interested", "question", "price_objection", "not_interested", "wrong_person", "needs_time"
    ]
    sentiment: str = Field(min_length=1, max_length=40)
    objection: str | None = Field(default=None, max_length=20_000)
    buying_stage: str = Field(min_length=1, max_length=80)
    recommended_action: str = Field(min_length=1, max_length=20_000)
    suggested_reply: str = Field(min_length=1, max_length=20_000)
    ai_request_id: UUID


class SalesAnalysisRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    conversation_reference: str
    intent: str
    sentiment: str
    objection: str | None
    buying_stage: str
    recommended_action: str
    suggested_reply: str
    ai_request_id: UUID


class AIModelPolicyCreate(BaseModel):
    organization_id: UUID
    task_type: str = Field(min_length=1, max_length=100)
    preferred_model: str = Field(min_length=1, max_length=200)
    fallback_model: str | None = Field(default=None, max_length=200)
    quality_requirement: Literal["economy", "balanced", "premium"]


class AIModelPolicyRead(ReadModel):
    organization_id: UUID
    task_type: str
    preferred_model: str
    fallback_model: str | None
    quality_requirement: str


class GrowthDashboardRead(BaseModel):
    organization_id: UUID
    prospects_discovered: int
    qualified_prospects: int
    opportunities_found: int
    gifts_created: int
    outreach_drafts: int
    replies: int
    customers: int
