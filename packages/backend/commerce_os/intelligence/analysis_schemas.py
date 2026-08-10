from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Score = float


class SignalAnalysisCreate(BaseModel):
    organization_id: UUID
    signal_id: UUID
    analysis_type: Literal[
        "market_impact", "timing", "customer_relevance", "commercial_relevance", "combined"
    ]
    market_impact: str = Field(min_length=1, max_length=10_000)
    timing_assessment: str = Field(min_length=1, max_length=10_000)
    customer_relevance: str = Field(min_length=1, max_length=10_000)
    commercial_relevance: str = Field(min_length=1, max_length=10_000)
    confidence_score: float = Field(ge=0, le=1)


class SignalAnalysisRead(ReadModel):
    organization_id: UUID
    signal_id: UUID
    analysis_type: str
    market_impact: str
    timing_assessment: str
    customer_relevance: str
    commercial_relevance: str
    confidence_score: float


class OpportunityAssessmentCreate(BaseModel):
    organization_id: UUID
    market_opportunity_id: UUID
    demand_score: float = Field(ge=0, le=100)
    timing_score: float = Field(ge=0, le=100)
    evidence_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    commercial_score: float = Field(ge=0, le=100)
    explanation: str = Field(min_length=1, max_length=20_000)


class OpportunityAssessmentRead(ReadModel):
    organization_id: UUID
    market_opportunity_id: UUID
    demand_score: float
    timing_score: float
    evidence_score: float
    risk_score: float
    commercial_score: float
    overall_score: float
    explanation: str
    formula_version: str


class OpportunityReportCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    title: str = Field(min_length=1, max_length=250)
    summary: str = Field(min_length=1, max_length=20_000)
    evidence_summary: str = Field(min_length=1, max_length=20_000)
    recommended_actions: list[str] = Field(min_length=1, max_length=100)
    risk_summary: str = Field(min_length=1, max_length=20_000)


class OpportunityReportUpdate(BaseModel):
    status: Literal["review", "presented"]


class OpportunityReportRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    title: str
    summary: str
    evidence_summary: str
    recommended_actions: list[str]
    risk_summary: str
    status: str
    decision_queue_item_id: UUID | None


class ReportQueueCreate(BaseModel):
    organization_id: UUID
    priority: Literal["low", "medium", "high", "critical"]
