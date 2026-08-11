from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class PlanCreate(BaseModel):
    organization_id: UUID
    project_id: UUID
    channel: str = Field(min_length=1, max_length=50)
    creative_asset_id: UUID
    objective: str = Field(min_length=1, max_length=5000)
    target_audience: str = Field(min_length=1, max_length=5000)
    execution_type: Literal["organic", "paid_test", "experiment"]
    created_by: UUID


class PlanUpdate(BaseModel):
    organization_id: UUID
    objective: str | None = Field(default=None, min_length=1, max_length=5000)
    target_audience: str | None = Field(default=None, min_length=1, max_length=5000)
    status: Literal["ready", "approved", "active", "paused", "completed", "cancelled"] | None = None
    approval_request_id: UUID | None = None


class PlanRead(ReadModel):
    organization_id: UUID
    project_id: UUID
    channel: str
    creative_asset_id: UUID
    objective: str
    target_audience: str
    execution_type: str
    status: str
    created_by: UUID
    approval_request_id: UUID | None


class ExperimentCreate(BaseModel):
    organization_id: UUID
    channel_execution_plan_id: UUID
    hypothesis: str = Field(min_length=1, max_length=5000)
    creative_variant_ids: list[UUID] = Field(min_length=1, max_length=100)
    success_metrics: list[str] = Field(min_length=1, max_length=100)
    test_notes: str = Field(default="", max_length=5000)


class ExperimentUpdate(BaseModel):
    organization_id: UUID
    hypothesis: str | None = Field(default=None, min_length=1, max_length=5000)
    success_metrics: list[str] | None = Field(default=None, min_length=1, max_length=100)
    test_notes: str | None = Field(default=None, max_length=5000)
    status: Literal["ready", "completed", "cancelled"] | None = None


class ExperimentRead(ReadModel):
    organization_id: UUID
    channel_execution_plan_id: UUID
    hypothesis: str
    creative_variant_ids: list[str]
    success_metrics: list[str]
    test_notes: str
    status: str


class DistributionCreate(BaseModel):
    organization_id: UUID
    creative_asset_id: UUID
    channel: str = Field(min_length=1, max_length=50)
    scheduled_time: datetime | None = None


class DistributionUpdate(BaseModel):
    organization_id: UUID
    distribution_status: Literal["ready", "approved", "published", "paused", "completed"] | None = (
        None
    )
    published_reference: str | None = Field(default=None, min_length=1, max_length=500)
    scheduled_time: datetime | None = None
    actual_time: datetime | None = None
    approval_request_id: UUID | None = None


class DistributionRead(ReadModel):
    organization_id: UUID
    creative_asset_id: UUID
    channel: str
    distribution_status: str
    published_reference: str | None
    scheduled_time: datetime | None
    actual_time: datetime | None
    approval_request_id: UUID | None


class PerformanceCreate(BaseModel):
    organization_id: UUID
    channel: str = Field(min_length=1, max_length=50)
    creative_asset_id: UUID
    experiment_id: UUID | None = None
    metric_name: str = Field(min_length=1, max_length=100)
    metric_value: Decimal = Field(max_digits=19)
    source: str = Field(min_length=1, max_length=200)
    observed_at: datetime


class PerformanceRead(ReadModel):
    organization_id: UUID
    channel: str
    creative_asset_id: UUID
    experiment_id: UUID | None
    metric_name: str
    metric_value: Decimal
    source: str
    observed_at: datetime
