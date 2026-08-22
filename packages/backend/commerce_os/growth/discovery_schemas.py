from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class DiscoverySourceCreate(BaseModel):
    organization_id: UUID
    source_type: Literal["google_maps", "website", "instagram", "linkedin", "manual"]
    source_name: str = Field(min_length=1, max_length=160)
    capability: str = Field(min_length=1, max_length=100)
    status: Literal["active", "disabled"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoverySourceRead(ReadModel):
    organization_id: UUID
    source_type: str
    source_name: str
    capability: str
    status: str
    source_metadata: dict[str, Any]


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
