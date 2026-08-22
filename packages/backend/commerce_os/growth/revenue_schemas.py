from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.growth.conversation_learning_schemas import ObjectionType
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
    source_candidate_id: UUID | None


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
        "website_conversion",
        "seo",
        "google_business",
        "social_media",
        "content",
        "branding",
        "customer_retention",
        "reputation_management",
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
    purchase_probability: float | None = Field(default=None, ge=0, le=1)
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
    purchase_probability: float | None
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
    evidence_reference: list[UUID] = Field(min_length=1)
    observed_issue: str = Field(default="", max_length=20_000)
    recommended_improvement: str = Field(default="", max_length=20_000)
    expected_value: str = Field(default="", max_length=20_000)
    preview_type: Literal["website", "social", "seo", "google_profile", "other"] = "other"
    preview_status: Literal["draft", "ready", "reviewed"] = "draft"


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
    evidence_reference: list[str]
    observed_issue: str
    recommended_improvement: str
    expected_value: str
    preview_type: str
    preview_status: str


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
    subject_options: list[str] = Field(min_length=1, max_length=5)
    opening_sentence: str = Field(min_length=1, max_length=2_000)
    personalized_context: str = Field(min_length=1, max_length=5_000)
    problem_observation: str = Field(min_length=1, max_length=5_000)
    gift_explanation: str = Field(min_length=1, max_length=5_000)
    soft_cta: str = Field(min_length=1, max_length=2_000)


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
    subject_options: list[str]
    opening_sentence: str
    personalized_context: str
    problem_observation: str
    gift_explanation: str
    soft_cta: str


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
    customer_reply: str = Field(min_length=1, max_length=20_000)
    buying_signal: str = Field(min_length=1, max_length=80)
    objection_type: ObjectionType | None = None
    urgency: Literal["low", "medium", "high", "unknown"] = "unknown"


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
    customer_reply: str
    buying_signal: str
    objection_type: str | None
    urgency: str
    status: str


class AIModelPolicyCreate(BaseModel):
    organization_id: UUID
    task_type: Literal[
        "prospect_research",
        "business_analysis",
        "customer_reply_analysis",
        "prospect_summarization",
        "evidence_classification",
        "draft_variations",
        "opportunity_evaluation",
        "final_outreach_polishing",
        "conversation_classification",
        "conversation_sentiment",
        "conversation_tagging",
        "complex_customer_reasoning",
        "reply_drafting",
        "negotiation_preparation",
    ]
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
    research_runs: int = 0
    top_opportunities: list[dict[str, object]] = Field(default_factory=list)
    average_qualification_score: float | None = None
    pending_human_review: int = 0
    active_revenue_experiments: int = 0
    prospects_awaiting_review: int = 0
    growth_gifts_ready: int = 0
    outreach_waiting_approval: int = 0
    replies_received: int = 0
    positive_conversations: int = 0
    conversion_signals: int = 0


class BusinessGrowthProfileCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    business_identity: dict[str, str]
    evidence_references: list[UUID] = Field(min_length=1)
    digital_presence: dict[str, object]
    customer_signals: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    growth_opportunities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class BusinessGrowthProfileRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    business_identity: dict[str, str]
    industry: str
    location: str | None
    evidence_references: list[str]
    digital_presence: dict[str, object]
    customer_signals: list[str]
    strengths: list[str]
    weaknesses: list[str]
    growth_opportunities: list[str]
    confidence: float


class ProspectRankingCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    pain_severity: float | None = Field(default=None, ge=0, le=100)
    business_impact: float | None = Field(default=None, ge=0, le=100)
    accessibility: float | None = Field(default=None, ge=0, le=100)
    buying_signals: float | None = Field(default=None, ge=0, le=100)
    solution_fit: float | None = Field(default=None, ge=0, le=100)


class ProspectRankingRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    pain_severity: float | None
    business_impact: float | None
    accessibility: float | None
    buying_signals: float | None
    solution_fit: float | None
    score: float | None
    missing_inputs: list[str]
    explanation: str
    formula_version: str


class GrowthRevenueV2Dashboard(BaseModel):
    organization_id: UUID
    business_profiles: int
    ranked_prospects: int
    pipeline: dict[str, int]
    growth_demand_signals: int
    commerce_independent_demand_signals: int
