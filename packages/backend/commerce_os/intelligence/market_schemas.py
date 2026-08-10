from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Platform = Literal[
    "reddit",
    "amazon_review",
    "etsy_review",
    "google_trends",
    "pinterest_trends",
    "news",
    "social_media",
]


class MarketSourceCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=160)
    platform: Platform
    source_type: Literal["community", "review", "trend", "news", "social"]
    access_method: Literal["manual", "file_import", "future_connector"]
    reliability_score: float = Field(ge=0, le=1)


class MarketSourceUpdate(BaseModel):
    status: Literal["inactive", "active", "archived"]


class MarketSourceRead(ReadModel):
    organization_id: UUID
    name: str
    platform: str
    source_type: str
    access_method: str
    reliability_score: float
    status: str


class MarketSignalCreate(BaseModel):
    organization_id: UUID
    source_id: UUID
    region: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=150)
    signal_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=10_000)
    trend_direction: Literal["rising", "falling", "stable"]
    confidence_score: float = Field(ge=0, le=1)
    observed_at: datetime


class MarketSignalUpdate(BaseModel):
    status: Literal["validated", "archived"]


class MarketSignalRead(ReadModel):
    organization_id: UUID
    source_id: UUID
    region: str
    category: str
    signal_type: str
    title: str
    description: str
    trend_direction: str
    confidence_score: float
    observed_at: datetime
    status: str


class MarketEvidenceCreate(BaseModel):
    organization_id: UUID
    signal_id: UUID
    evidence_type: Literal["observation", "reference", "dataset", "document"]
    content_reference: str = Field(min_length=1, max_length=500)
    strength_score: float = Field(ge=0, le=1)
    captured_at: datetime


class MarketEvidenceRead(ReadModel):
    organization_id: UUID
    signal_id: UUID
    evidence_type: str
    content_reference: str
    strength_score: float
    captured_at: datetime


class MarketClusterCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=150)
    confidence: float = Field(ge=0, le=1)
    impact_score: float = Field(ge=0, le=100)


class MarketClusterRead(ReadModel):
    organization_id: UUID
    name: str
    category: str
    confidence: float
    impact_score: float


class ClusterMembershipCreate(BaseModel):
    organization_id: UUID
    signal_id: UUID


class ClusterMembershipRead(ReadModel):
    organization_id: UUID
    cluster_id: UUID
    signal_id: UUID


class OpportunityLinkCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID


class OpportunityLinkRead(ReadModel):
    organization_id: UUID
    signal_id: UUID
    opportunity_id: UUID
