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


class ResearchCitationRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    evidence_type: str
    evidence_id: UUID
    source_reference: str
    citation_note: str
    relevance_score: float


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
