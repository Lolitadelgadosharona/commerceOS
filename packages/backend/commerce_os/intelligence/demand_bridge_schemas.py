from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

DemandSourceType = Literal[
    "growthos_conversation",
    "reddit",
    "amazon_review",
    "etsy_review",
    "google_trend",
    "social_comment",
    "competitor_review",
    "research_analysis",
    "manual_input",
    "news_event",
    "weather_environment",
    "seasonal_pattern",
]
DemandSourceCategory = Literal[
    "customer_voice",
    "marketplace",
    "search",
    "social",
    "news",
    "weather",
    "seasonality",
    "manual",
    "research",
]


class DemandSignalSourceCreate(BaseModel):
    organization_id: UUID
    source_type: DemandSourceType
    display_name: str = Field(min_length=1, max_length=150)
    source_domain: Literal["growth", "intelligence", "research", "manual"]
    collection_method: str = Field(min_length=1, max_length=80)
    evidence_origin: str = Field(min_length=1, max_length=250)
    source_category: DemandSourceCategory = "customer_voice"
    geographic_scope: str | None = Field(default=None, max_length=200)
    time_window: str | None = Field(default=None, max_length=120)
    trend_type: Literal["rising", "falling", "stable", "volatile", "seasonal"] | None = None


class DemandSignalSourceRead(ReadModel):
    organization_id: UUID
    source_type: str
    display_name: str
    source_domain: str
    collection_method: str
    evidence_origin: str
    source_category: str
    geographic_scope: str | None
    time_window: str | None
    trend_type: str | None
    status: str


class BusinessDemandEvidenceInput(BaseModel):
    source_id: UUID
    source_reference: str = Field(min_length=1, max_length=500)
    evidence_text: str = Field(min_length=1, max_length=20_000)


class PredictiveDemandInput(BaseModel):
    prediction_type: str = Field(min_length=1, max_length=80)
    forecast_window: str = Field(min_length=1, max_length=120)
    confidence_score: float = Field(ge=0, le=1)
    assumptions: list[str] = Field(min_length=1)
    uncertainty_notes: str = Field(min_length=1, max_length=20_000)


class BusinessDemandSignalCreate(BaseModel):
    organization_id: UUID
    source_type: DemandSourceType
    source_reference: str = Field(min_length=1, max_length=500)
    customer_segment: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=80)
    problem_statement: str = Field(min_length=1, max_length=20_000)
    customer_language: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    confidence_basis: str = Field(min_length=1, max_length=20_000)
    evidence: list[BusinessDemandEvidenceInput] = Field(min_length=1)
    prediction: PredictiveDemandInput | None = None


class DemandAggregationCreate(BaseModel):
    organization_id: UUID
    learning_signal_ids: list[UUID] = Field(min_length=1)
    customer_segment: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=80)


class DemandSignalTransition(BaseModel):
    status: Literal["review", "approved", "rejected"]
    approval_request_id: UUID | None = None


class DemandSignalRead(ReadModel):
    organization_id: UUID
    source_domain: str
    source_reference_id: UUID
    source_type: str
    source_reference: str
    collection_method: str
    evidence_origin: str
    confidence_basis: str
    customer_segment: str
    category: str
    problem_statement: str
    customer_language: str
    frequency: int
    confidence: float
    evidence_count: int
    status: str


class DemandSignalEvidenceRead(ReadModel):
    organization_id: UUID
    demand_signal_id: UUID
    source_type: str
    source_id: UUID
    source_reference: str
    evidence_text: str


class DemandDashboardItem(BaseModel):
    demand_signal_id: UUID
    category: str
    customer_segment: str
    problem_statement: str
    frequency: int
    confidence: float
    evidence_count: int
    source_type: str
    evidence_sources: list[str]
    source_conversation_ids: list[UUID]


class DemandSourceVolume(BaseModel):
    source_type: str
    signal_count: int
    evidence_count: int
    average_confidence: float
    signal_percentage: float


class EmergingDemandCategory(BaseModel):
    category: str
    signal_count: int
    total_frequency: int
    average_confidence: float


class CustomerPainClusterOverview(BaseModel):
    cluster_id: UUID
    name: str
    category: str
    severity_score: float
    confidence_score: float
    status: str


class DemandThemeAnalysisCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    signal_ids: list[UUID] = Field(min_length=1)
    summary: str = Field(min_length=1, max_length=20_000)


class DemandThemeAnalysisRead(ReadModel):
    organization_id: UUID
    name: str
    category: str
    evidence_count: int
    signal_diversity: int
    confidence: float
    evidence_strength: str
    summary: str


class EmergingDemandTheme(BaseModel):
    theme_analysis_id: UUID
    name: str
    category: str
    evidence_count: int
    signal_diversity: int
    confidence: float
    evidence_strength: str


class PredictiveIndicator(BaseModel):
    demand_signal_id: UUID
    upcoming_trend: str
    timeframe: str
    evidence_sources: list[str]
    confidence: float
    uncertainty: str


class DemandDashboardRead(BaseModel):
    organization_id: UUID
    draft_signals: int
    signals_in_review: int
    approved_signals: int
    source_overview: list[DemandSourceVolume]
    emerging_categories: list[EmergingDemandCategory]
    customer_pain_clusters: list[CustomerPainClusterOverview]
    emerging_demand_themes: list[EmergingDemandTheme]
    predictive_indicators: list[PredictiveIndicator]
    emerging_customer_pains: list[DemandDashboardItem]
