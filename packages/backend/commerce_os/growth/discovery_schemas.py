from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class DiscoverySourceCreate(BaseModel):
    organization_id: UUID
    source_type: Literal[
        "google_maps",
        "google_business_profile",
        "website",
        "reviews",
        "instagram",
        "tiktok",
        "reddit",
        "yelp",
        "google_trends",
        "news",
        "linkedin",
        "manual",
        "other",
    ]
    source_name: str = Field(min_length=1, max_length=160)
    capability: str = Field(min_length=1, max_length=100)
    status: Literal["active", "disabled"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    adapter_key: str = Field(default="manual", min_length=1, max_length=120)
    collection_mode: Literal["human_review", "controlled_import", "controlled_connector"] = (
        "human_review"
    )


class DiscoverySourceRead(ReadModel):
    organization_id: UUID
    source_type: str
    source_name: str
    capability: str
    status: str
    source_metadata: dict[str, Any]
    adapter_key: str
    collection_mode: str


class WebsiteEvidenceCreate(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    source_id: UUID
    source_url: str = Field(min_length=1, max_length=1000)
    business_name: str = Field(min_length=1, max_length=250)
    location: str | None = Field(default=None, max_length=250)
    services: list[str] = Field(default_factory=list)
    website_structure: dict[str, Any] = Field(default_factory=dict)
    homepage_signals: dict[str, Any] = Field(default_factory=dict)
    booking_flow_signals: dict[str, Any] = Field(default_factory=dict)
    seo_signals: dict[str, Any] = Field(default_factory=dict)
    geo_visibility_signals: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime
    confidence: float = Field(ge=0, le=1)


class WebsiteEvidenceRead(ReadModel, WebsiteEvidenceCreate):
    pass


class BusinessProfileEvidenceCreate(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    source_id: UUID
    source_reference: str = Field(min_length=1, max_length=1000)
    review_count: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    location: str | None = Field(default=None, max_length=250)
    business_category: str | None = Field(default=None, max_length=160)
    customer_language: list[str] = Field(default_factory=list)
    captured_at: datetime
    confidence: float = Field(ge=0, le=1)


class BusinessProfileEvidenceRead(ReadModel, BusinessProfileEvidenceCreate):
    pass


class InstagramEvidenceCreate(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    source_id: UUID
    profile_reference: str = Field(min_length=1, max_length=1000)
    profile_information: dict[str, Any] = Field(default_factory=dict)
    posting_frequency: str | None = Field(default=None, max_length=120)
    content_themes: list[str] = Field(default_factory=list)
    brand_signals: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime
    confidence: float = Field(ge=0, le=1)


class InstagramEvidenceRead(ReadModel, InstagramEvidenceCreate):
    pass


class ProspectPipelineRead(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    candidate_status: str
    evidence_count: int
    growth_prospect_id: UUID | None
    growth_profile_id: UUID | None
    opportunity_ids: list[UUID]
    growth_gift_ids: list[UUID]
    outreach_draft_ids: list[UUID]
    next_step: str


class OperatorRevenueDashboard(BaseModel):
    organization_id: UUID
    day: str
    daily_prospects_discovered: int
    qualified_prospects: int
    growth_opportunities: int
    gifts_ready: int
    outreach_drafts_ready: int
    replies: int
    positive_conversations: int
    revenue_experiments: int
    estimated_ai_cost: float
    ai_cost_currency: str | None


class DiscoveryRunCreate(BaseModel):
    organization_id: UUID
    source_id: UUID
    query: str = Field(min_length=1, max_length=20_000)
    target_industry: str = Field(min_length=1, max_length=160)
    target_location: str = Field(min_length=1, max_length=250)


class DiscoveryRunRead(ReadModel):
    organization_id: UUID
    source_id: UUID
    query: str
    target_industry: str
    target_location: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_by: UUID
    failure_reason: str | None


class CandidateCreate(BaseModel):
    organization_id: UUID
    discovery_run_id: UUID
    business_name: str = Field(min_length=1, max_length=250)
    website: str | None = Field(default=None, max_length=500)
    location: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=160)
    source_reference: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)


class CandidateRead(ReadModel):
    organization_id: UUID
    discovery_run_id: UUID
    business_name: str
    website: str | None
    location: str
    category: str
    source_reference: str
    confidence: float
    duplicate_key: str
    status: str


class ResearchEvidenceCreate(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    evidence_type: str = Field(min_length=1, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    observation: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    collected_at: datetime


class ResearchEvidenceRead(ReadModel):
    organization_id: UUID
    candidate_id: UUID
    evidence_type: str
    source_url: str | None
    observation: str
    confidence: float
    collected_at: datetime


class BusinessResearchStart(BaseModel):
    organization_id: UUID
    capability_id: UUID
    prompt_version_id: UUID | None = None


class BusinessResearchRunRead(ReadModel):
    organization_id: UUID
    candidate_id: UUID
    status: str
    capability_id: UUID
    prompt_version_id: UUID | None
    ai_request_id: UUID | None
    created_by: UUID
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    methodology_version: str


class BusinessResearchResultRead(ReadModel):
    organization_id: UUID
    research_run_id: UUID
    summary: str
    business_profile: dict[str, Any]
    evidence_summary: list[dict[str, Any]]
    potential_growth_issues: list[str]
    confidence: float
    missing_information: list[str]
    risk: list[str]


class QualificationInputs(BaseModel):
    organization_id: UUID
    pain_signal: float | None = Field(default=None, ge=0, le=100)
    purchase_probability: float | None = Field(default=None, ge=0, le=100)
    accessibility: float | None = Field(default=None, ge=0, le=100)
    quick_win_potential: float | None = Field(default=None, ge=0, le=100)


class QualificationRead(ReadModel):
    organization_id: UUID
    candidate_id: UUID
    score: float | None
    calculation_inputs: dict[str, float | None]
    missing_inputs: list[str]
    explanation: str
    formula_version: str


class BusinessDemandSignalRead(ReadModel):
    organization_id: UUID
    source_domain: str
    industry: str
    signal_type: str
    description: str
    evidence_reference: list[str]
    confidence: float
    source_research_result_id: UUID


class GrowthDiscoveryDashboardRead(BaseModel):
    organization_id: UUID
    prospects_discovered: int
    research_runs: int
    qualified_prospects: int
    top_opportunities: list[dict[str, Any]]
    average_qualification_score: float | None
    pending_human_review: int
