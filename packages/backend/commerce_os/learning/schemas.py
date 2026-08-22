from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from commerce_os.shared.schemas import ReadModel

SourceType = Literal[
    "customer_signal",
    "conversation_signal",
    "support_signal",
    "growth_performance",
    "creative_performance",
    "channel_performance",
    "revenue_observation",
    "cost_observation",
    "contribution_profit",
    "refund_signal",
    "dispute_signal",
    "product_risk",
    "market_signal",
    "growth_conversation_analysis",
]


class LearningObservationCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    product_id: UUID | None = None
    source_type: SourceType
    source_record_id: UUID
    observation_type: str = Field(min_length=1, max_length=80)
    observed_at: datetime
    evidence_reference: str = Field(min_length=1, max_length=500)
    confidence: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=200)


class LearningObservationRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    product_id: UUID | None
    source_domain: str
    source_type: str
    source_record_id: UUID
    observation_type: str
    observed_at: datetime
    evidence_reference: str
    confidence: float | None
    metadata: dict[str, Any] = Field(validation_alias="observation_metadata")


class EvidenceLinkInput(BaseModel):
    observation_id: UUID
    evidence_role: Literal["supporting", "contradicting"]


class HypothesisCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    product_id: UUID | None = None
    hypothesis: str = Field(min_length=1, max_length=10_000)
    target_type: str = Field(min_length=1, max_length=50)
    target_id: UUID | None = None
    category: str = Field(min_length=1, max_length=60)
    evidence_links: list[EvidenceLinkInput] = Field(min_length=1)
    evidence_coverage: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    methodology_version: str = Field(min_length=1, max_length=80)


class HypothesisTransition(BaseModel):
    status: Literal["under_review", "supported", "rejected"]


class HypothesisRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    product_id: UUID | None
    hypothesis: str
    target_type: str
    target_id: UUID | None
    category: str
    evidence_coverage: float
    confidence: float
    status: str
    methodology_version: str


class ConclusionCreate(BaseModel):
    organization_id: UUID
    hypothesis_id: UUID
    conclusion: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)
    methodology_version: str = Field(min_length=1, max_length=80)


class ConclusionTransition(BaseModel):
    status: Literal["supported", "rejected"]
    review_metadata: dict[str, Any] = Field(default_factory=dict, max_length=100)


class ConclusionRead(ReadModel):
    organization_id: UUID
    hypothesis_id: UUID
    conclusion: str
    supporting_observation_ids: list[str]
    contradicting_observation_ids: list[str]
    confidence: float
    evidence_coverage: float
    methodology_version: str
    status: str
    reviewer_id: UUID | None
    reviewed_at: datetime | None
    review_metadata: dict[str, Any]


class RecommendationCreate(BaseModel):
    organization_id: UUID
    conclusion_id: UUID
    target_type: Literal[
        "product",
        "listing",
        "geo_content",
        "creative",
        "channel",
        "customer_support",
        "sales",
        "logistics",
        "pricing",
        "supplier",
        "experiment",
    ]
    target_id: UUID | None = None
    recommendation: str = Field(min_length=1, max_length=10_000)
    rationale: str = Field(min_length=1, max_length=10_000)


class RecommendationRead(ReadModel):
    organization_id: UUID
    conclusion_id: UUID
    target_type: str
    target_id: UUID | None
    recommendation: str
    rationale: str
    status: str
    decision_queue_item_id: UUID | None


class PriorityInputs(BaseModel):
    expected_commercial_impact: float | None = Field(default=None, ge=0, le=100)
    evidence_confidence: float | None = Field(default=None, ge=0, le=100)
    customer_frequency: float | None = Field(default=None, ge=0, le=100)
    customer_severity: float | None = Field(default=None, ge=0, le=100)
    financial_impact: float | None = Field(default=None, ge=0, le=100)
    refund_risk: float | None = Field(default=None, ge=0, le=100)
    dispute_risk: float | None = Field(default=None, ge=0, le=100)
    implementation_effort: float | None = Field(default=None, ge=0, le=100)
    reversibility: float | None = Field(default=None, ge=0, le=100)
    testability: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def require_evidence(self) -> "PriorityInputs":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("At least one priority input is required.")
        return self


class PriorityCreate(BaseModel):
    organization_id: UUID
    recommendation_id: UUID
    inputs: PriorityInputs


class PriorityRead(ReadModel):
    organization_id: UUID
    recommendation_id: UUID
    formula_version: str
    supplied_inputs: dict[str, float | None]
    missing_inputs: list[str]
    calculated_score: float
    explanation_components: dict[str, Any]


class FeedbackLoopRead(BaseModel):
    observation: list[LearningObservationRead]
    hypothesis: HypothesisRead | None
    conclusion: ConclusionRead | None
    recommendation: RecommendationRead | None
    priority: PriorityRead | None
    decision_queue_item_id: UUID | None
    missing_stages: list[str]


class LearningDashboardRead(BaseModel):
    organization_id: UUID
    advisory: bool = True
    active_hypotheses: int
    supported_conclusions: int
    highest_priority_improvements: list[dict[str, Any]]
    recurring_customer_problems: int
    revenue_leakage_signals: int
    refund_dispute_signals: int
    creative_channel_signals: int
    unresolved_evidence_gaps: int
