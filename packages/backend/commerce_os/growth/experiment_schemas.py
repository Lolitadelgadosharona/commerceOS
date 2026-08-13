from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Channel = Literal["tiktok", "instagram", "pinterest", "facebook", "youtube", "reddit"]


class GrowthExperimentCreate(BaseModel):
    organization_id: UUID
    project_id: UUID
    creative_strategy_id: UUID
    hypothesis: str = Field(min_length=1, max_length=10_000)
    objective: str = Field(min_length=1, max_length=10_000)
    audience: str = Field(min_length=1, max_length=10_000)
    channel: Channel


class GrowthExperimentTransition(BaseModel):
    status: Literal["review", "approved", "active", "completed", "cancelled"]
    approval_request_id: UUID | None = None


class GrowthExperimentRead(ReadModel):
    organization_id: UUID
    project_id: UUID
    creative_strategy_id: UUID
    hypothesis: str
    objective: str
    audience: str
    channel: str
    status: str
    owner_id: UUID
    approval_request_id: UUID | None


class ExperimentVariantCreate(BaseModel):
    organization_id: UUID
    experiment_id: UUID
    creative_asset_id: UUID
    variant_name: str = Field(min_length=1, max_length=150)
    hypothesis: str = Field(min_length=1, max_length=10_000)
    expected_outcome: str = Field(min_length=1, max_length=10_000)


class ExperimentVariantRead(ReadModel):
    organization_id: UUID
    experiment_id: UUID
    creative_asset_id: UUID
    variant_name: str
    hypothesis: str
    expected_outcome: str


class DistributionCampaignCreate(BaseModel):
    organization_id: UUID
    experiment_id: UUID
    creative_asset_id: UUID
    channel: Channel


class DistributionCampaignTransition(BaseModel):
    lifecycle_state: Literal["review", "approved", "active", "completed", "cancelled"]
    approval_request_id: UUID | None = None


class DistributionCampaignRead(ReadModel):
    organization_id: UUID
    experiment_id: UUID
    creative_asset_id: UUID
    channel: str
    approval_state: str
    lifecycle_state: str
    approval_request_id: UUID | None


class GrowthPerformanceCreate(BaseModel):
    organization_id: UUID
    creative_asset_id: UUID
    experiment_id: UUID
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    engagement: Decimal = Field(ge=0, max_digits=19)
    conversion: Decimal = Field(ge=0, max_digits=19)
    revenue_observation_id: UUID | None = None
    confidence: float = Field(ge=0, le=1)


class GrowthPerformanceRead(ReadModel):
    organization_id: UUID
    creative_asset_id: UUID
    experiment_id: UUID
    impressions: int
    clicks: int
    engagement: Decimal
    conversion: Decimal
    revenue_observation_id: UUID | None
    confidence: float


class GrowthLearningSignalCreate(BaseModel):
    organization_id: UUID
    source_experiment_id: UUID
    observation_ids: list[UUID] = Field(min_length=1)
    pattern_reference_id: UUID | None = None
    pattern: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)
    recommendation: str = Field(min_length=1, max_length=10_000)


class GrowthLearningSignalRead(ReadModel):
    organization_id: UUID
    source_experiment_id: UUID
    pattern_reference_id: UUID | None
    pattern: str
    confidence: float
    recommendation: str
