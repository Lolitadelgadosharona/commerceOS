from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

RiskValue = Literal["low", "medium", "high", "critical"]


class MarketOpportunityCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=5000)
    category: str = Field(min_length=1, max_length=150)
    market: str = Field(min_length=1, max_length=150)
    geography: str = Field(min_length=1, max_length=150)
    trigger_type: Literal[
        "weather_event",
        "seasonal_event",
        "cultural_event",
        "customer_pain",
        "trend_shift",
        "regulatory_change",
        "supply_change",
    ]
    timing_window: str = Field(min_length=1, max_length=200)
    status: Literal["observed", "evaluating", "qualified", "rejected", "archived"] = "observed"
    confidence_score: float = Field(ge=0, le=1)


class MarketOpportunityUpdate(BaseModel):
    status: Literal["observed", "evaluating", "qualified", "rejected", "archived"]


class MarketOpportunityRead(ReadModel):
    organization_id: UUID
    title: str
    description: str
    category: str
    market: str
    geography: str
    trigger_type: str
    timing_window: str
    status: str
    confidence_score: float


class OpportunityEvidenceCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    source_type: Literal[
        "customer_signal", "search_trend", "news", "review", "social", "market_report"
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    evidence_summary: str = Field(min_length=1, max_length=5000)
    confidence_score: float = Field(ge=0, le=1)


class OpportunityEvidenceRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    source_type: str
    source_reference: str
    evidence_summary: str
    confidence_score: float


class ProductCandidateCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    product_name: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=150)
    customer_need: str = Field(min_length=1, max_length=5000)
    estimated_margin: float = Field(ge=0, le=1)
    risk_level: RiskValue
    status: Literal["proposed", "reviewing", "selected", "rejected"] = "proposed"


class ProductCandidateRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID | None
    opportunity_candidate_id: UUID | None = None
    product_name: str
    category: str
    customer_need: str
    target_customer: str = ""
    product_description: str = ""
    value_proposition: str = ""
    confidence_score: float = 0
    estimated_margin: float
    risk_level: str
    status: str


class ValueRange(BaseModel):
    minimum: float = Field(ge=0)
    maximum: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class ProductEvidenceInput(BaseModel):
    evidence_source: Literal[
        "demand_signal",
        "opportunity_evidence",
        "marketplace_evidence",
        "customer_conversation",
        "research_analysis",
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    evidence_summary: str = Field(min_length=1, max_length=20_000)
    relevance: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0, le=1)


RiskBand = Literal["low", "medium", "high", "critical"]


class ProductOpportunityCandidateCreate(BaseModel):
    organization_id: UUID
    opportunity_candidate_id: UUID
    product_name: str = Field(min_length=1, max_length=250)
    product_category: str = Field(min_length=1, max_length=150)
    customer_problem: str = Field(min_length=1, max_length=20_000)
    target_customer: str = Field(min_length=1, max_length=5000)
    product_description: str = Field(min_length=1, max_length=20_000)
    value_proposition: str = Field(min_length=1, max_length=20_000)
    confidence_score: float = Field(ge=0, le=1)
    demand_fit_score: float = Field(ge=0, le=100)
    problem_solution_fit: float = Field(ge=0, le=100)
    estimated_price_range: ValueRange
    estimated_cost_range: ValueRange
    gross_margin_estimate: float = Field(ge=0, le=1)
    shipping_complexity: RiskBand
    fulfillment_risk: RiskBand
    ip_risk: RiskBand
    regulatory_risk: RiskBand
    payment_risk: RiskBand
    dispute_risk: RiskBand
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    evidence: list[ProductEvidenceInput] = Field(min_length=1)


class ProductEvaluationRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    demand_fit_score: float
    problem_solution_fit: float
    estimated_price_range: dict[str, object]
    estimated_cost_range: dict[str, object]
    gross_margin_estimate: float
    shipping_complexity: str
    fulfillment_risk: str
    ip_risk: str
    regulatory_risk: str
    payment_risk: str
    dispute_risk: str
    strengths: list[str]
    weaknesses: list[str]
    assumptions: list[str]
    missing_information: list[str]
    evaluation_score: float
    recommendation: str
    formula_version: str


class ProductCandidateEvidenceRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    evidence_source: str
    source_reference: str
    evidence_summary: str
    relevance: str
    confidence: float


class ProductCandidateReview(BaseModel):
    action: Literal["accept", "reject"]
    approval_request_id: UUID | None = None


class ProductEvaluationDashboard(BaseModel):
    candidate_products: list[ProductCandidateRead]
    economics_view: list[ProductEvaluationRead]
    validation_queue: list[ProductCandidateRead]


class OpportunityScoreCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    demand_score: float = Field(ge=0, le=100)
    pain_score: float = Field(ge=0, le=100)
    trend_score: float = Field(ge=0, le=100)
    margin_score: float = Field(ge=0, le=100)
    competition_score: float = Field(ge=0, le=100)
    ip_risk_score: float = Field(ge=0, le=100)
    dispute_risk_score: float = Field(ge=0, le=100)


class OpportunityScoreRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    demand_score: float
    pain_score: float
    trend_score: float
    margin_score: float
    competition_score: float
    ip_risk_score: float
    dispute_risk_score: float
    overall_score: float
    formula_version: str


class OpportunityRiskCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    risk_type: Literal["trademark", "brand", "policy", "dispute", "payment"]
    severity: RiskValue
    description: str = Field(min_length=1, max_length=5000)
    status: Literal["open", "mitigated", "accepted", "dismissed"] = "open"


class OpportunityRiskRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    risk_type: str
    severity: str
    description: str
    status: str
