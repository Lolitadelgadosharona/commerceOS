from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

DiscoveryType = Literal[
    "reddit_pain_discovery",
    "marketplace_review_discovery",
    "trend_opportunity_discovery",
    "cross_source_opportunity_discovery",
]
DiscoveryEvidenceType = Literal[
    "market_signal",
    "pain_candidate",
    "pain_cluster",
    "marketplace_review",
    "research_analysis",
    "customer_need",
]


class DiscoveryEvidenceInput(BaseModel):
    evidence_type: DiscoveryEvidenceType
    evidence_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class OpportunityDiscoveryRunCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    discovery_type: DiscoveryType
    objective: str = Field(min_length=1, max_length=20_000)
    methodology_version: str = Field(default="governed-opportunity-discovery-v1", max_length=80)
    research_run_id: UUID | None = None
    capability_id: UUID
    prompt_version_id: UUID | None = None
    evidence: list[DiscoveryEvidenceInput] = Field(min_length=1)


class OpportunityDiscoveryRunRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    discovery_type: str
    objective: str
    status: str
    methodology_version: str
    research_run_id: UUID | None
    capability_id: UUID
    prompt_version_id: UUID | None
    ai_request_id: UUID | None
    created_by: UUID
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None


class OpportunityCandidateRead(ReadModel):
    organization_id: UUID
    discovery_run_id: UUID | None
    title: str
    category: str
    problem_statement: str
    customer_segment: str
    opportunity_description: str
    market_context: str
    evidence_summary: str
    evidence_references: list[dict[str, Any]]
    solution_direction: str
    customer_language: list[str]
    confidence_score: float
    risk_summary: list[str]
    open_questions: list[str]
    missing_evidence: list[str]
    advisory_score: float
    status: str
    methodology_version: str
    decision_queue_item_id: UUID | None


OpportunityEvidenceType = Literal[
    "customer_pain",
    "marketplace",
    "search",
    "social",
    "news",
    "weather",
    "seasonal",
    "growth_conversation",
    "research",
]


class OpportunityCandidateCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=150)
    customer_segment: str = Field(min_length=1, max_length=5000)
    customer_problem: str = Field(min_length=1, max_length=20_000)
    opportunity_description: str = Field(min_length=1, max_length=20_000)
    solution_direction: str = Field(min_length=1, max_length=20_000)
    market_context: str = Field(min_length=1, max_length=20_000)
    demand_signal_ids: list[UUID] = Field(min_length=1)
    market_timing: str = Field(min_length=1, max_length=5000)
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class OpportunityCandidateEvidenceRead(ReadModel):
    organization_id: UUID
    opportunity_candidate_id: UUID
    demand_signal_id: UUID
    evidence_type: str
    evidence_summary: str
    contribution: str
    confidence: float


class OpportunityCandidateAssessmentRead(ReadModel):
    organization_id: UUID
    opportunity_candidate_id: UUID
    demand_strength: str
    signal_diversity: int
    market_timing: str
    confidence: float
    risks: list[str]
    missing_information: list[str]
    assumptions: list[str]


class OpportunityReview(BaseModel):
    action: Literal["accept", "reject"]
    approval_request_id: UUID | None = None


class OpportunityThemeRead(BaseModel):
    category: str
    evidence_count: int
    source_diversity: int
    confidence: float


class OpportunityDiscoveryDashboard(BaseModel):
    opportunity_themes: list[OpportunityThemeRead]
    emerging_opportunities: list[OpportunityCandidateRead]
    review_queue: list[OpportunityCandidateRead]


class DiscoveryTemplateRead(BaseModel):
    discovery_type: DiscoveryType
    purpose: str
    evidence_requirements: list[DiscoveryEvidenceType]
    expected_output_schema: dict[str, Any]
