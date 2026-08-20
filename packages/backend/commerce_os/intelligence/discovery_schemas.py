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
    discovery_run_id: UUID
    title: str
    problem_statement: str
    customer_segment: str
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


class DiscoveryTemplateRead(BaseModel):
    discovery_type: DiscoveryType
    purpose: str
    evidence_requirements: list[DiscoveryEvidenceType]
    expected_output_schema: dict[str, Any]
