from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.build.creative_asset_models import CreativeAssetType
from commerce_os.shared.schemas import ReadModel

ProviderType = Literal["image", "video", "voice", "editing"]


class GenerationRequestCreate(BaseModel):
    organization_id: UUID
    creative_brief_id: UUID
    asset_type: CreativeAssetType
    platform: str = Field(min_length=1, max_length=50)
    objective: str = Field(min_length=1, max_length=5000)
    generation_parameters: dict[str, Any] = Field(default_factory=dict, max_length=200)
    requested_by: UUID


class GenerationRequestUpdate(BaseModel):
    organization_id: UUID
    status: Literal["submitted", "cancelled"]


class GenerationRequestRead(ReadModel):
    organization_id: UUID
    creative_brief_id: UUID
    asset_type: str
    platform: str
    objective: str
    generation_parameters: dict[str, Any]
    requested_by: UUID
    status: str


class ProviderCapabilityCreate(BaseModel):
    organization_id: UUID
    provider_name: str = Field(min_length=1, max_length=150)
    provider_type: ProviderType
    capabilities: list[str] = Field(min_length=1, max_length=100)
    cost_model: dict[str, Any] = Field(default_factory=dict, max_length=100)
    availability: bool
    status: Literal["active", "inactive", "deprecated"] = "active"


class ProviderCapabilityRead(ReadModel):
    organization_id: UUID
    provider_name: str
    provider_type: str
    capabilities: list[str]
    cost_model: dict[str, Any]
    availability: bool
    status: str


class GenerationJobCreate(BaseModel):
    organization_id: UUID
    request_id: UUID
    provider: UUID
    input_reference: str = Field(min_length=1, max_length=500)
    estimated_cost: Decimal = Field(ge=0, max_digits=19)


class GenerationJobRead(ReadModel):
    organization_id: UUID
    request_id: UUID
    provider: UUID = Field(validation_alias="provider_id")
    status: str
    input_reference: str
    output_reference: str | None
    estimated_cost: Decimal
    actual_cost: Decimal | None
    latency: float | None
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    retry_count: int


class QualityReviewCreate(BaseModel):
    organization_id: UUID
    asset_id: UUID
    review_type: str = Field(min_length=1, max_length=50)
    score: float = Field(ge=0, le=100)
    issues: list[str] = Field(default_factory=list, max_length=100)
    recommendation: str = Field(min_length=1, max_length=5000)


class QualityReviewRead(ReadModel):
    organization_id: UUID
    asset_id: UUID
    review_type: str
    score: float
    issues: list[str]
    recommendation: str
