from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

AdvisoryOutput = Literal["recommendation", "draft", "analysis", "candidate", "classification"]
AnalysisStatus = Literal["draft", "in_review", "reviewed", "rejected", "cancelled"]
EvidenceType = Literal[
    "market_data_record",
    "marketplace_review",
    "normalized_marketplace_review",
    "customer_signal",
    "pain_cluster",
    "market_signal",
    "competitive_observation",
    "opportunity_evidence",
    "customer_language",
    "research_citation",
]


class ResearchAnalysisCreate(BaseModel):
    organization_id: UUID
    ai_request_id: UUID
    analysis_type: str = Field(min_length=1, max_length=60)
    output_classification: AdvisoryOutput
    output_summary: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    methodology_version: str = Field(min_length=1, max_length=80)


class ResearchAnalysisTransition(BaseModel):
    status: AnalysisStatus


class ResearchAnalysisRead(ReadModel):
    organization_id: UUID
    ai_request_id: UUID
    analysis_type: str
    output_classification: str
    output_summary: str
    confidence: float
    methodology_version: str
    status: str
    reviewed_by: UUID | None


class ResearchCitationCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    evidence_type: EvidenceType
    evidence_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    citation_note: str = Field(min_length=1, max_length=5000)
    relevance_score: float = Field(ge=0, le=1)
    citation_location: str | None = Field(default=None, max_length=500)
    methodology_version: str | None = Field(default=None, max_length=80)
    missing_evidence: bool = False


class ResearchCitationRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    evidence_type: str
    evidence_id: UUID
    source_reference: str
    citation_note: str
    relevance_score: float
    citation_location: str | None
    methodology_version: str | None
    missing_evidence: bool


ResearchType = Literal[
    "product_opportunity_discovery",
    "customer_pain_analysis",
    "market_trend_analysis",
    "competitor_research",
    "geo_content_research",
]
RunEvidenceType = Literal[
    "market_signal",
    "marketplace_review",
    "pain_cluster",
    "customer_language",
    "opportunity_evidence",
    "research_citation",
]


class ResearchRunEvidenceInput(BaseModel):
    evidence_type: RunEvidenceType
    evidence_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class ResearchRunCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    research_type: ResearchType
    objective: str = Field(min_length=1, max_length=20_000)
    methodology_version: str = Field(default="governed-research-v1", max_length=80)
    capability_id: UUID
    prompt_version_id: UUID | None = None
    evidence: list[ResearchRunEvidenceInput] = Field(default_factory=list)


class ResearchRunRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    research_type: str
    objective: str
    status: str
    methodology_version: str
    created_by: UUID
    capability_id: UUID
    prompt_version_id: UUID | None
    ai_request_id: UUID | None
    analysis_id: UUID | None
    decision_queue_item_id: UUID | None
    started_at: Any | None
    completed_at: Any | None
    failure_reason: str | None


class ResearchRunResult(BaseModel):
    run: ResearchRunRead
    analysis: ResearchAnalysisRead | None
    execution: dict[str, Any] | None
    usage_cost: dict[str, Any] | None


class ResearchTemplateRead(BaseModel):
    research_type: ResearchType
    goal: str
    evidence_requirements: list[RunEvidenceType]
    output_classification: Literal["analysis", "candidate", "classification", "draft"]
    expected_output_schema: dict[str, Any]


class CustomerPainResearchCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    pain_patterns: list[str] = Field(min_length=1)
    customer_needs: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    motivations: list[str] = Field(default_factory=list)
    language_themes: list[str] = Field(default_factory=list)


class CustomerPainResearchRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    pain_patterns: list[str]
    customer_needs: list[str]
    objections: list[str]
    motivations: list[str]
    language_themes: list[str]


class MarketInsightResearchCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    market_trends: list[str] = Field(default_factory=list)
    emerging_signals: list[str] = Field(default_factory=list)
    competitive_observations: list[str] = Field(default_factory=list)
    opportunity_indicators: list[str] = Field(default_factory=list)


class MarketInsightResearchRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    market_trends: list[str]
    emerging_signals: list[str]
    competitive_observations: list[str]
    opportunity_indicators: list[str]


class OpportunityResearchBriefCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    opportunity_id: UUID
    opportunity_summary: str = Field(min_length=1, max_length=20_000)
    customer_problem: str = Field(min_length=1, max_length=10_000)
    market_context: str = Field(min_length=1, max_length=10_000)
    competition: str = Field(min_length=1, max_length=10_000)
    risks: list[str] = Field(default_factory=list)
    economics_references: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class OpportunityResearchBriefRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    opportunity_id: UUID
    opportunity_summary: str
    customer_problem: str
    market_context: str
    competition: str
    risks: list[str]
    economics_references: list[dict[str, Any]]
    missing_information: list[str]
