from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

SourceType = Literal[
    "reddit",
    "amazon_review",
    "etsy_review",
    "shopify",
    "email",
    "social",
    "support",
    "b2b_conversation",
]
SignalKind = Literal[
    "quality_concern",
    "delivery_delay",
    "price_objection",
    "trust_concern",
    "feature_request",
]
SeverityValue = Literal["low", "medium", "high", "critical"]


class SignalSourceCreate(BaseModel):
    organization_id: UUID
    source_type: SourceType
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)


class SignalSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class SignalSourceRead(ReadModel):
    organization_id: UUID
    source_type: str
    name: str
    description: str
    is_active: bool


class CustomerSignalCreate(BaseModel):
    organization_id: UUID
    signal_source_id: UUID
    source_type: SourceType
    source_reference: str = Field(min_length=1, max_length=500)
    customer_id: UUID | None = None
    signal_type: SignalKind
    content_reference: str = Field(min_length=1, max_length=2000)
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    severity: SeverityValue
    confidence: float = Field(ge=0, le=1)


class CustomerSignalRead(ReadModel):
    organization_id: UUID
    signal_source_id: UUID
    source_type: str
    source_reference: str
    customer_id: UUID | None
    signal_type: str
    content_reference: str
    sentiment: str
    severity: str
    confidence: float


class CustomerVoiceClusterCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    signal_ids: list[UUID] = Field(min_length=1)
    severity: SeverityValue | None = None
    trend_direction: Literal["increasing", "stable", "decreasing", "unknown"] = "unknown"


class CustomerVoiceClusterRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    signal_count: int
    severity: str
    trend_direction: str


class CustomerInsightCreate(BaseModel):
    organization_id: UUID
    cluster_id: UUID | None = None
    signal_ids: list[UUID] = Field(min_length=1)
    title: str = Field(min_length=1, max_length=250)
    summary: str = Field(min_length=1, max_length=5000)
    impact_level: SeverityValue
    recommended_action: str = Field(min_length=1, max_length=5000)
    status: Literal["new", "validated", "actioned", "dismissed"] = "new"


class CustomerInsightUpdate(BaseModel):
    status: Literal["new", "validated", "actioned", "dismissed"]


class CustomerInsightRead(ReadModel):
    organization_id: UUID
    cluster_id: UUID | None
    title: str
    summary: str
    evidence_count: int
    impact_level: str
    recommended_action: str
    status: str
