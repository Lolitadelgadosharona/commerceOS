from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.build.creative_asset_models import CreativeAssetType
from commerce_os.shared.schemas import ReadModel


class CreativeAssetCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    asset_type: CreativeAssetType
    status: Literal["draft"] = "draft"
    source: str = Field(min_length=1, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=200)
    approval_status: Literal["pending"] = "pending"


class CreativeAssetRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    asset_type: str
    status: str
    source: str
    metadata: dict[str, Any] = Field(validation_alias="asset_metadata")
    approval_status: str


class CreativeAssetVersionCreate(BaseModel):
    organization_id: UUID
    asset_id: UUID
    variation_reason: str = Field(min_length=1, max_length=10_000)
    experiment_group: str = Field(min_length=1, max_length=100)


class CreativeAssetVersionRead(ReadModel):
    organization_id: UUID
    asset_id: UUID
    version_number: int
    variation_reason: str
    experiment_group: str


class CreativePerformanceCreate(BaseModel):
    organization_id: UUID
    asset_id: UUID
    metric_type: str = Field(min_length=1, max_length=100)
    metric_value: Decimal = Field(max_digits=19)
    source: str = Field(min_length=1, max_length=200)
    period: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)


class CreativePerformanceRead(ReadModel):
    organization_id: UUID
    asset_id: UUID
    metric_type: str
    metric_value: Decimal
    source: str
    period: str
    confidence: float
