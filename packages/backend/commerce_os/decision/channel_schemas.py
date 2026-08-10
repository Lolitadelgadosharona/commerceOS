from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from commerce_os.shared.schemas import ReadModel

Channel = Literal["tiktok", "instagram", "facebook", "pinterest", "google", "reddit"]
Mode = Literal["organic", "paid", "community", "search", "messaging", "hybrid"]


class StrategyCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    product_id: UUID
    creative_strategy_id: UUID | None = None
    market: str = Field(min_length=1, max_length=150)
    geography: str = Field(min_length=1, max_length=150)
    audience: str = Field(min_length=1, max_length=5000)
    business_model: Literal["b2c", "b2b"]
    objective: str = Field(min_length=1, max_length=5000)


class StrategyUpdate(BaseModel):
    status: Literal["recommended", "approved", "rejected", "archived"]


class StrategyRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    product_id: UUID
    creative_strategy_id: UUID | None
    market: str
    geography: str
    audience: str
    business_model: str
    objective: str
    status: str


class CandidateCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    channel: Channel
    distribution_mode: Mode
    suitability_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1)
    recommendation: Literal["recommended", "consider", "excluded"]
    reason: str | None = Field(default=None, max_length=5000)
    exclusion_reason: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def reasons(self) -> "CandidateCreate":
        if self.recommendation == "excluded" and not self.exclusion_reason:
            raise ValueError("excluded channels require exclusion_reason")
        if self.recommendation != "excluded" and not self.reason:
            raise ValueError("recommended/considered channels require reason")
        return self


class CandidateRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    channel: str
    distribution_mode: str
    suitability_score: float
    confidence_score: float
    recommendation: str
    reason: str | None
    exclusion_reason: str | None


FACTORS = (
    "target_customer_fit",
    "product_fit",
    "buying_intent",
    "visual_fit",
    "organic_potential",
    "search_discovery_potential",
    "content_cost",
    "competition",
    "expected_acquisition_cost",
    "historical_performance_confidence",
    "conversion_path_fit",
)


class ScoreCreate(BaseModel):
    organization_id: UUID
    candidate_id: UUID
    target_customer_fit: float | None = Field(default=None, ge=0, le=100)
    product_fit: float | None = Field(default=None, ge=0, le=100)
    buying_intent: float | None = Field(default=None, ge=0, le=100)
    visual_fit: float | None = Field(default=None, ge=0, le=100)
    organic_potential: float | None = Field(default=None, ge=0, le=100)
    search_discovery_potential: float | None = Field(default=None, ge=0, le=100)
    content_cost: float | None = Field(default=None, ge=0, le=100)
    competition: float | None = Field(default=None, ge=0, le=100)
    expected_acquisition_cost: float | None = Field(default=None, ge=0, le=100)
    historical_performance_confidence: float | None = Field(default=None, ge=0, le=100)
    conversion_path_fit: float | None = Field(default=None, ge=0, le=100)


class ScoreRead(ReadModel):
    organization_id: UUID
    candidate_id: UUID
    target_customer_fit: float | None
    product_fit: float | None
    buying_intent: float | None
    visual_fit: float | None
    organic_potential: float | None
    search_discovery_potential: float | None
    content_cost: float | None
    competition: float | None
    expected_acquisition_cost: float | None
    historical_performance_confidence: float | None
    conversion_path_fit: float | None
    overall_score: float
    evidence_coverage: float
    formula_version: str


class PathCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    name: str = Field(min_length=1, max_length=250)


class PathRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    name: str
    business_model: str
    status: str


class StepCreate(BaseModel):
    organization_id: UUID
    path_id: UUID
    sequence: int = Field(ge=1)
    step_type: Literal[
        "content",
        "ad",
        "search_discovery",
        "community_interaction",
        "landing_page",
        "product_page",
        "checkout",
        "lead_form",
        "message",
        "qualification",
        "quote",
        "order",
    ]
    channel: Channel | None = None
    responsible_domain: Literal["growth", "operations", "governance", "finance"]
    human_required: bool = False
    approval_required: bool = False


class StepRead(ReadModel):
    organization_id: UUID
    path_id: UUID
    sequence: int
    step_type: str
    channel: str | None
    responsible_domain: str
    human_required: bool
    approval_required: bool


Metric = Literal[
    "impressions",
    "reach",
    "engagement",
    "hold_rate",
    "completion_rate",
    "clicks",
    "ctr",
    "cpc",
    "qualified_leads",
    "cpl",
    "sessions",
    "add_to_cart",
    "checkout_started",
    "purchases",
    "cvr",
    "revenue",
    "media_cost",
    "roas",
    "contribution_profit",
    "refund_rate",
    "dispute_rate",
    "ltv",
]


class MeasurementCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    metrics: list[Metric] = Field(min_length=1)
    notes: str = Field(default="", max_length=5000)


class MeasurementRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    metrics: list[str]
    notes: str


class EvidenceCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    evidence_type: Literal[
        "customer_intelligence",
        "opportunity_intelligence",
        "product_intelligence",
        "listing_geo_intelligence",
        "creative_strategy",
        "historical_channel_observation",
        "market_research",
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=5000)
    confidence_score: float = Field(ge=0, le=1)


class EvidenceRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    evidence_type: str
    source_reference: str
    summary: str
    confidence_score: float
