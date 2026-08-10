from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

RiskLevel = Literal["low", "medium", "high", "critical"]
Intent = Literal[
    "buying_intent",
    "product_question",
    "price_objection",
    "quality_concern",
    "delivery_concern",
    "trust_concern",
    "support_request",
    "refund_request",
    "negotiation",
]


class SalesProfileCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    conversation_id: UUID
    product_id: UUID | None = None
    intent: Intent
    estimated_value: float | None = Field(default=None, ge=0)
    repeat_probability: float | None = Field(default=None, ge=0, le=1)
    risk_level: RiskLevel | None = None


class SalesProfileRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    conversation_id: UUID
    product_id: UUID | None
    intent: str
    estimated_value: float | None
    repeat_probability: float | None
    risk_level: str | None


class RecommendationCreate(BaseModel):
    organization_id: UUID
    sales_profile_id: UUID
    recommendation_type: Literal[
        "product_recommendation",
        "objection_handling",
        "follow_up",
        "qualification",
        "escalation",
    ]
    reason: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)


class RecommendationUpdate(BaseModel):
    status: Literal["reviewed", "accepted", "rejected"]


class RecommendationRead(ReadModel):
    organization_id: UUID
    sales_profile_id: UUID
    recommendation_type: str
    reason: str
    confidence: float
    status: str


class SupportIntelligenceCreate(BaseModel):
    organization_id: UUID
    conversation_id: UUID
    issue_category: Literal["delivery", "quality", "product_usage", "payment", "refund", "other"]
    severity: RiskLevel
    customer_impact: str = Field(min_length=1, max_length=10_000)
    risk_level: RiskLevel
    recommended_resolution: str = Field(min_length=1, max_length=10_000)


class SupportIntelligenceRead(ReadModel):
    organization_id: UUID
    conversation_id: UUID
    issue_category: str
    severity: str
    customer_impact: str
    risk_level: str
    recommended_resolution: str


class RiskSignalCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    risk_type: Literal["refund_risk", "dispute_risk", "churn_risk", "fraud_risk"]
    severity: RiskLevel
    evidence_reference: str = Field(min_length=1, max_length=500)


class RiskSignalRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    risk_type: str
    severity: str
    evidence_reference: str
