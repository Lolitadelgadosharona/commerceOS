from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

TemplateType = Literal["listing_strategy", "geo_content", "listing_geo_combined"]
EvidenceType = Literal[
    "customer_language", "pain_cluster", "customer_need", "marketplace_review", "research_analysis"
]


class ListingEvidenceInput(BaseModel):
    evidence_type: EvidenceType
    evidence_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class ListingIntelligenceRunCreate(BaseModel):
    organization_id: UUID
    product_id: UUID | None = None
    opportunity_candidate_id: UUID | None = None
    objective: str = Field(min_length=1, max_length=20_000)
    template_type: TemplateType
    capability_id: UUID
    prompt_version_id: UUID | None = None
    methodology_version: str = Field(default="governed-listing-geo-v1", max_length=80)
    evidence: list[ListingEvidenceInput] = Field(min_length=1)


class ListingIntelligenceRunRead(ReadModel):
    organization_id: UUID
    product_id: UUID | None
    opportunity_candidate_id: UUID | None
    objective: str
    template_type: str
    status: str
    capability_id: UUID
    prompt_version_id: UUID | None
    ai_request_id: UUID | None
    methodology_version: str
    created_by: UUID
    completed_at: datetime | None
    failure_reason: str | None


class ListingStrategyRecommendationRead(ReadModel):
    organization_id: UUID
    listing_run_id: UUID
    customer_segment: str
    primary_problem: str
    positioning: str
    unique_value: str
    benefits: list[str]
    feature_translation: list[dict[str, Any]]
    trust_elements: list[str]
    objections: list[str]
    competitive_difference: str
    confidence: float
    evidence_refs: list[dict[str, Any]]


class GEOContentRecommendationRead(ReadModel):
    organization_id: UUID
    listing_run_id: UUID
    entity_description: str
    important_attributes: list[str]
    customer_questions: list[str]
    answer_strategy: str
    comparison_topics: list[str]
    expert_topics: list[str]
    citation_targets: list[dict[str, Any]]
    missing_information: list[str]
    confidence: float


class FAQRecommendationRead(ReadModel):
    organization_id: UUID
    listing_run_id: UUID
    question: str
    customer_intent: str
    answer_outline: str
    evidence: list[dict[str, Any]]
    risk: str
