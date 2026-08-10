from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Priority = Literal["low", "medium", "high", "critical"]


class ProductLaunchCreate(BaseModel):
    organization_id: UUID
    project_id: UUID
    product_id: UUID
    market: str = Field(min_length=1, max_length=120)
    priority: Priority


class ProductLaunchUpdate(BaseModel):
    status: Literal["approved", "in_progress", "blocked", "completed", "cancelled"]
    approval_request_id: UUID | None = None


class ProductLaunchRead(ReadModel):
    organization_id: UUID
    project_id: UUID
    product_id: UUID
    market: str
    status: str
    priority: str
    approval_request_id: UUID | None


class LaunchMilestoneCreate(BaseModel):
    organization_id: UUID
    launch_id: UUID
    name: Literal[
        "product_approval",
        "supplier_ready",
        "listing_ready",
        "creative_ready",
        "channel_ready",
        "launch_ready",
    ]
    sequence: int = Field(ge=1)
    due_date: date | None = None
    owner_role_id: UUID | None = None


class LaunchMilestoneUpdate(BaseModel):
    status: Literal["in_progress", "blocked", "done"]


class LaunchMilestoneRead(ReadModel):
    organization_id: UUID
    launch_id: UUID
    name: str
    sequence: int
    status: str
    due_date: date | None
    owner_role_id: UUID | None


class ExecutionTaskCreate(BaseModel):
    organization_id: UUID
    launch_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    owner_type: Literal["ai", "human", "team"]
    priority: Priority


class ExecutionTaskUpdate(BaseModel):
    status: Literal["in_progress", "blocked", "done"]


class ExecutionTaskRead(ReadModel):
    organization_id: UUID
    launch_id: UUID
    title: str
    description: str
    owner_type: str
    priority: str
    status: str


class ActionPlanCreate(BaseModel):
    organization_id: UUID
    plan_date: date
    related_launch_id: UUID
    priority: Priority
    summary: str = Field(min_length=1, max_length=10_000)
    generated_from: str = Field(min_length=1, max_length=120)


class ActionPlanRead(ReadModel):
    organization_id: UUID
    plan_date: date
    related_launch_id: UUID
    priority: str
    summary: str
    generated_from: str


class ExecutionBlockerCreate(BaseModel):
    organization_id: UUID
    launch_id: UUID
    reason: str = Field(min_length=1, max_length=10_000)
    severity: Literal["low", "medium", "high", "critical"]
    impact: str = Field(min_length=1, max_length=10_000)


class ExecutionBlockerUpdate(BaseModel):
    status: Literal["acknowledged", "resolved"]


class ExecutionBlockerRead(ReadModel):
    organization_id: UUID
    launch_id: UUID
    reason: str
    severity: str
    impact: str
    status: str
