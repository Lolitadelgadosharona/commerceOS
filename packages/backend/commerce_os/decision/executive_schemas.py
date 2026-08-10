from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Domain = Literal[
    "intelligence", "decision", "build", "growth", "operations", "finance", "learning", "governance"
]
MetricType = Literal["revenue", "profit", "customer", "product", "creative", "channel", "risk"]


class ExecutiveMetricCreate(BaseModel):
    organization_id: UUID
    metric_type: MetricType
    metric_name: str = Field(min_length=1, max_length=160)
    value: float
    unit: str = Field(min_length=1, max_length=40)
    source_domain: Domain
    period_id: UUID


class ExecutiveMetricRead(ReadModel):
    organization_id: UUID
    metric_type: str
    metric_name: str
    value: float
    unit: str
    source_domain: str
    period_id: UUID


class OperatingSignalCreate(BaseModel):
    organization_id: UUID
    domain: Domain
    severity: Literal["info", "warning", "critical"]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    impact: str = Field(min_length=1, max_length=10_000)
    recommendation: str = Field(min_length=1, max_length=10_000)


class OperatingSignalUpdate(BaseModel):
    status: Literal["acknowledged", "resolved"]


class OperatingSignalRead(ReadModel):
    organization_id: UUID
    domain: str
    severity: str
    title: str
    description: str
    impact: str
    recommendation: str
    status: str


class OperatingReviewCreate(BaseModel):
    organization_id: UUID
    period_id: UUID
    summary: str = Field(min_length=1, max_length=20_000)
    key_findings: list[str] = Field(min_length=1, max_length=100)
    risks: list[str] = Field(max_length=100)
    recommended_actions: list[str] = Field(max_length=100)
    confidence: float = Field(ge=0, le=1)


class OperatingReviewUpdate(BaseModel):
    status: Literal["reviewed", "archived"]


class OperatingReviewRead(ReadModel):
    organization_id: UUID
    period_id: UUID
    summary: str
    key_findings: list[str]
    risks: list[str]
    recommended_actions: list[str]
    status: str
    confidence: float
