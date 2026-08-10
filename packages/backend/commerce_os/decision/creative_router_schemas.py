from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Capability = Literal["image", "video", "voice", "editing"]


class AssetStrategyCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    creative_strategy_id: UUID
    audience: str = Field(min_length=1, max_length=5000)
    objective: str = Field(min_length=1, max_length=5000)
    recommended_format: Literal[
        "video", "image", "carousel", "ugc", "testimonial", "educational", "comparison"
    ]
    creative_angle: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0, le=1)


class AssetStrategyUpdate(BaseModel):
    status: Literal["recommended", "approved", "archived"]


class AssetStrategyRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    creative_strategy_id: UUID
    audience: str
    objective: str
    recommended_format: str
    creative_angle: str
    confidence: float
    status: str


class ModelProviderCreate(BaseModel):
    organization_id: UUID
    provider_name: str = Field(min_length=1, max_length=150)
    capability_type: Capability
    quality_score: float = Field(ge=0, le=100)
    cost_score: float = Field(ge=0, le=100)
    speed_score: float = Field(ge=0, le=100)
    availability: bool
    status: Literal["active", "inactive", "deprecated"] = "active"


class ModelProviderRead(ReadModel):
    organization_id: UUID
    provider_name: str
    capability_type: str
    quality_score: float
    cost_score: float
    speed_score: float
    availability: bool
    status: str


class RoutingDecisionCreate(BaseModel):
    organization_id: UUID
    asset_strategy_id: UUID
    capability_required: Capability
    candidate_provider_ids: list[UUID] = Field(min_length=1)
    platform_suitability: dict[UUID, float] = Field(default_factory=dict)
    historical_performance: dict[UUID, float] = Field(default_factory=dict)
    reason: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0, le=1)


class RoutingDecisionRead(ReadModel):
    organization_id: UUID
    asset_strategy_id: UUID
    capability_required: str
    selected_provider_id: UUID
    reason: str
    confidence: float
    factor_snapshot: dict[str, float | None]
    routing_score: float
    router_version: str


class EconomicAssessmentCreate(BaseModel):
    organization_id: UUID
    creative_strategy_id: UUID
    estimated_production_cost: float = Field(ge=0)
    expected_impact: float = Field(ge=0)
    test_value: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)


class EconomicAssessmentRead(ReadModel):
    organization_id: UUID
    creative_strategy_id: UUID
    estimated_production_cost: float
    expected_impact: float
    test_value: float
    profitability_score: float
    confidence: float
    formula_version: str


class PatternCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=250)
    pattern_type: Literal["hook_pattern", "story_structure", "cta_pattern", "proof_structure"]
    description: str = Field(min_length=1, max_length=10_000)
    source_reference: str = Field(min_length=1, max_length=500)
    performance_notes: str = Field(default="", max_length=10_000)


class PatternRead(ReadModel):
    organization_id: UUID
    name: str
    pattern_type: str
    description: str
    source_reference: str
    performance_notes: str
