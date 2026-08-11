from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class JobStateUpdate(BaseModel):
    organization_id: UUID
    status: Literal[
        "queued", "running", "validating", "succeeded", "failed", "retrying", "cancelled"
    ]
    failure_reason: str | None = Field(default=None, min_length=1, max_length=5000)


class ExecutionRecordCreate(BaseModel):
    organization_id: UUID
    generation_job_id: UUID
    provider: UUID
    execution_status: Literal[
        "queued", "running", "validating", "succeeded", "failed", "retrying", "cancelled"
    ]
    input_snapshot: dict[str, Any] = Field(default_factory=dict, max_length=200)
    output_reference: str | None = Field(default=None, min_length=1, max_length=500)
    estimated_cost: Decimal = Field(ge=0, max_digits=19)
    actual_cost: Decimal | None = Field(default=None, ge=0, max_digits=19)
    duration: float = Field(ge=0)


class ExecutionRecordRead(ReadModel):
    organization_id: UUID
    generation_job_id: UUID
    provider: UUID = Field(validation_alias="provider_id")
    execution_status: str
    input_snapshot: dict[str, Any]
    output_reference: str | None
    estimated_cost: Decimal
    actual_cost: Decimal | None
    duration: float


class CreativeArtifactCreate(BaseModel):
    organization_id: UUID
    generation_job_id: UUID
    asset_id: UUID
    artifact_type: str = Field(min_length=1, max_length=30)
    artifact_reference: str = Field(min_length=1, max_length=500)
    validation_status: Literal["pending", "valid", "invalid"] = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=200)


class CreativeArtifactRead(ReadModel):
    organization_id: UUID
    generation_job_id: UUID
    asset_id: UUID
    artifact_type: str
    artifact_reference: str
    validation_status: str
    metadata: dict[str, Any] = Field(validation_alias="artifact_metadata")


class GenerationCostCreate(BaseModel):
    organization_id: UUID
    provider: UUID
    job: UUID
    estimated_cost: Decimal = Field(ge=0, max_digits=19)
    actual_cost: Decimal = Field(ge=0, max_digits=19)
    currency: str = Field(min_length=3, max_length=3, pattern="^[A-Z]{3}$")


class GenerationCostRead(ReadModel):
    organization_id: UUID
    provider: UUID = Field(validation_alias="provider_id")
    job: UUID = Field(validation_alias="job_id")
    estimated_cost: Decimal
    actual_cost: Decimal
    currency: str
    timestamp: datetime
