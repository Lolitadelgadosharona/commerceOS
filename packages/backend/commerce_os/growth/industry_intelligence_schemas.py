from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

PatternType = Literal[
    "customer_problem",
    "website",
    "seo",
    "geo",
    "social",
    "review",
    "pricing",
    "seasonality",
    "buying_trigger",
    "objection",
    "competitive",
    "service_outcome",
]
ServiceType = Literal["website_growth", "seo", "geo", "social_growth", "review_growth"]


class IndustryProfileCreate(BaseModel):
    organization_id: UUID
    industry_key: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=200)
    vertical: str = Field(min_length=1, max_length=120)
    scope_notes: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)


class IndustryProfileRead(ReadModel):
    organization_id: UUID
    industry_key: str
    display_name: str
    vertical: str
    scope_notes: str
    status: str
    confidence: float


class IndustryEvidenceCreate(BaseModel):
    organization_id: UUID
    industry_profile_id: UUID
    evidence_type: str = Field(min_length=1, max_length=80)
    source_reference: str = Field(min_length=1, max_length=1000)
    observation: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    captured_at: datetime


class IndustryEvidenceRead(ReadModel):
    organization_id: UUID
    industry_profile_id: UUID
    evidence_type: str
    source_reference: str
    observation: str
    confidence: float
    captured_at: datetime


class IndustryPatternCreate(BaseModel):
    organization_id: UUID
    industry_profile_id: UUID
    pattern_type: PatternType
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=20_000)
    evidence_references: list[UUID] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class IndustryPatternRead(ReadModel):
    organization_id: UUID
    industry_profile_id: UUID
    pattern_type: str
    title: str
    description: str
    evidence_references: list[str]
    confidence: float
    status: str


class GEOAssessmentCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    industry_profile_id: UUID | None = None
    website_signals: dict[str, object] = Field(default_factory=dict)
    social_signals: dict[str, object] = Field(default_factory=dict)
    review_signals: dict[str, object] = Field(default_factory=dict)
    visibility_gaps: list[str] = Field(min_length=1)
    recommendations: list[str] = Field(min_length=1)
    evidence_references: list[UUID] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class GEOAssessmentRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    industry_profile_id: UUID | None
    website_signals: dict[str, object]
    social_signals: dict[str, object]
    review_signals: dict[str, object]
    visibility_gaps: list[str]
    recommendations: list[str]
    evidence_references: list[str]
    confidence: float


class ServiceRecommendationCreate(BaseModel):
    organization_id: UUID
    prospect_id: UUID
    industry_profile_id: UUID | None = None
    opportunity_id: UUID | None = None
    service_type: ServiceType
    customer_problem: str = Field(min_length=1, max_length=20_000)
    recommended_scope: str = Field(min_length=1, max_length=20_000)
    expected_value: str = Field(min_length=1, max_length=20_000)
    purchase_probability: float | None = Field(default=None, ge=0, le=1)
    quick_win_potential: Literal["low", "medium", "high", "unknown"] = "unknown"
    evidence_references: list[UUID] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ServiceRecommendationRead(ReadModel):
    organization_id: UUID
    prospect_id: UUID
    industry_profile_id: UUID | None
    opportunity_id: UUID | None
    service_type: str
    customer_problem: str
    recommended_scope: str
    expected_value: str
    purchase_probability: float | None
    quick_win_potential: str
    evidence_references: list[str]
    confidence: float
    status: str


class IndustryLearningSignalCreate(BaseModel):
    organization_id: UUID
    industry_profile_id: UUID
    source_type: Literal[
        "conversation",
        "objection",
        "purchased_service",
        "failed_offer",
        "successful_offer",
        "manual_review",
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    pattern_type: PatternType
    observation: str = Field(min_length=1, max_length=20_000)
    evidence_references: list[UUID] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class IndustryLearningSignalRead(ReadModel):
    organization_id: UUID
    industry_profile_id: UUID
    source_type: str
    source_reference: str
    pattern_type: str
    observation: str
    evidence_references: list[str]
    confidence: float
    status: str
