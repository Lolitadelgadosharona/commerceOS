from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class CreativeStrategyCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    target_audience: str = Field(min_length=1, max_length=5000)
    marketing_objective: str = Field(min_length=1, max_length=5000)
    core_message: str = Field(min_length=1, max_length=5000)
    emotional_angle: str = Field(min_length=1, max_length=5000)
    creative_direction: str = Field(min_length=1, max_length=5000)


class CreativeStrategyUpdate(BaseModel):
    status: Literal["approved", "active", "archived"]


class CreativeStrategyRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    target_audience: str
    marketing_objective: str
    core_message: str
    emotional_angle: str
    creative_direction: str
    status: str


class CreativeHypothesisCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    hypothesis: str = Field(min_length=1, max_length=5000)
    expected_behavior: str = Field(min_length=1, max_length=5000)
    success_metric: str = Field(min_length=1, max_length=250)
    confidence_score: float = Field(ge=0, le=1)
    status: Literal["proposed", "validated", "rejected", "archived"] = "proposed"


class CreativeHypothesisRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    hypothesis: str
    expected_behavior: str
    success_metric: str
    confidence_score: float
    status: str


class CreativeBriefCreate(BaseModel):
    organization_id: UUID
    strategy_id: UUID
    platform: Literal["tiktok", "instagram", "facebook", "pinterest", "google"]
    audience: str = Field(min_length=1, max_length=5000)
    hook: str = Field(min_length=1, max_length=5000)
    story_structure: str = Field(min_length=1, max_length=5000)
    proof_points: str = Field(min_length=1, max_length=5000)
    cta: str = Field(min_length=1, max_length=5000)
    content_format: Literal["video", "image", "carousel", "ugc", "testimonial", "educational"]


class CreativeBriefRead(ReadModel):
    organization_id: UUID
    strategy_id: UUID
    platform: str
    audience: str
    hook: str
    story_structure: str
    proof_points: str
    cta: str
    content_format: str


class CreativeChannelFitCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    channel: Literal["tiktok", "instagram", "facebook", "pinterest", "google"]
    suitability_score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=5000)


class CreativeChannelFitRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    channel: str
    suitability_score: float
    reason: str


class CreativeExperimentCreate(BaseModel):
    organization_id: UUID
    hypothesis_id: UUID
    variant_name: str = Field(min_length=1, max_length=250)
    test_objective: str = Field(min_length=1, max_length=5000)
    metric: str = Field(min_length=1, max_length=250)


class CreativeExperimentUpdate(BaseModel):
    status: Literal["running", "completed"]
    result: str | None = Field(default=None, max_length=5000)


class CreativeExperimentRead(ReadModel):
    organization_id: UUID
    hypothesis_id: UUID
    variant_name: str
    test_objective: str
    metric: str
    result: str | None
    status: str
