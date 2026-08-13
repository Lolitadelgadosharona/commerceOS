from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Marketplace = Literal["amazon", "etsy"]
EvidenceTarget = Literal[
    "customer_signal", "pain_cluster", "customer_language", "opportunity_evidence"
]


class MarketplaceReviewCreate(BaseModel):
    organization_id: UUID
    connector_id: UUID
    ingestion_job_id: UUID | None = None
    source_record_id: UUID
    marketplace: Marketplace
    source_identity: str = Field(min_length=1, max_length=500)
    product_reference: str = Field(min_length=1, max_length=500)
    rating: float = Field(ge=0, le=5)
    review_date: datetime
    review_text_metadata: dict[str, Any] = Field(default_factory=dict)
    verified_indicator: bool | None = None


class MarketplaceReviewRead(ReadModel):
    organization_id: UUID
    connector_id: UUID
    ingestion_job_id: UUID | None
    source_record_id: UUID
    marketplace: str
    source_identity: str
    product_reference: str
    rating: float
    review_date: datetime
    review_text_metadata: dict[str, Any]
    verified_indicator: bool | None
    evidence_hash: str


class NormalizedMarketplaceReviewCreate(BaseModel):
    organization_id: UUID
    review_evidence_id: UUID
    sentiment_metadata: dict[str, Any] = Field(default_factory=dict)
    topic_metadata: dict[str, Any] = Field(default_factory=dict)
    customer_language: str = Field(min_length=1, max_length=10_000)
    product_reference: str = Field(min_length=1, max_length=500)
    evidence_confidence: float = Field(ge=0, le=1)


class NormalizedMarketplaceReviewRead(ReadModel):
    organization_id: UUID
    review_evidence_id: UUID
    sentiment_metadata: dict[str, Any]
    topic_metadata: dict[str, Any]
    customer_language: str
    product_reference: str
    evidence_confidence: float


class MarketplaceEvidenceLinkCreate(BaseModel):
    organization_id: UUID
    review_evidence_id: UUID
    target_type: EvidenceTarget
    target_id: UUID
    evidence_strength: float = Field(ge=0, le=1)


class MarketplaceEvidenceLinkRead(ReadModel):
    organization_id: UUID
    review_evidence_id: UUID
    target_type: str
    target_id: UUID
    evidence_strength: float


class CompetitiveObservationCreate(BaseModel):
    organization_id: UUID
    review_evidence_id: UUID
    competitor_reference: str = Field(min_length=1, max_length=500)
    product_observations: dict[str, Any] = Field(default_factory=dict)
    customer_preference_signals: list[str] = Field(default_factory=list)
    recurring_complaints: list[str] = Field(default_factory=list)
    observation_count: int = Field(default=1, ge=1)
    confidence: float = Field(ge=0, le=1)


class CompetitiveObservationRead(ReadModel):
    organization_id: UUID
    review_evidence_id: UUID
    competitor_reference: str
    product_observations: dict[str, Any]
    customer_preference_signals: list[str]
    recurring_complaints: list[str]
    observation_count: int
    confidence: float
