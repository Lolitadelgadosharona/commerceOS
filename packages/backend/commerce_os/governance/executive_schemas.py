from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class DecisionQueueCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=200)
    domain: Literal[
        "intelligence",
        "decision",
        "build",
        "growth",
        "operations",
        "finance",
        "learning",
        "governance",
    ]
    reason: str = Field(min_length=1, max_length=10_000)
    priority: Literal["low", "medium", "high", "critical"]
    required_action: Literal["approve", "review", "reject"]
    approval_request_id: UUID | None = None


class DecisionQueueUpdate(BaseModel):
    status: Literal["acknowledged", "closed"]


class DecisionQueueRead(ReadModel):
    organization_id: UUID
    title: str
    domain: str
    reason: str
    priority: str
    required_action: str
    status: str
    approval_request_id: UUID | None
