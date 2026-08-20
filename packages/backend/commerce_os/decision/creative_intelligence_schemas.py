from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

TemplateType = Literal[
    "pain_message", "transformation_message", "trust_message", "education_message"
]
EvidenceType = Literal["customer_language", "pain_cluster", "customer_need"]


class CreativeEvidenceInput(BaseModel):
    evidence_type: EvidenceType
    evidence_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class CreativeIntelligenceRunCreate(BaseModel):
    organization_id: UUID
    opportunity_candidate_id: UUID | None = None
    product_id: UUID | None = None
    objective: str = Field(min_length=1, max_length=20_000)
    template_type: TemplateType
    capability_id: UUID
    prompt_version_id: UUID | None = None
    methodology_version: str = Field(default="governed-creative-intelligence-v1", max_length=80)
    evidence: list[CreativeEvidenceInput] = Field(min_length=1)


class CreativeIntelligenceRunRead(ReadModel):
    organization_id: UUID
    opportunity_candidate_id: UUID | None
    product_id: UUID | None
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


class CreativeStrategyRecommendationRead(ReadModel):
    organization_id: UUID
    creative_run_id: UUID
    target_customer: str
    customer_problem: str
    core_message: str
    value_proposition: str
    emotional_angle: str
    rational_angle: str
    trust_elements: list[str]
    objections: list[str]
    channel_recommendations: list[str]
    confidence_score: float
    risks: list[str]
    estimated_impact: str | None
    output_type: str


class CreativeBriefRecommendationRead(ReadModel):
    organization_id: UUID
    creative_run_id: UUID
    hook: str
    problem: str
    solution: str
    proof: list[str]
    cta: str
    visual_direction: str
    video_concept: str
    image_concept: str
    ugc_concept: str
    audience: str
    channel: str
    evidence_references: list[dict[str, Any]]
