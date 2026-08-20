from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

IntentStage = Literal[
    "unknown", "aware", "interested", "considering", "high_intent", "customer", "repeat_customer"
]


class EvidenceReference(BaseModel):
    reference_type: Literal["journey_event", "conversation_intent", "customer_signal"]
    reference_id: UUID


class IntentJourneyCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    status: IntentStage = "unknown"
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class IntentJourneyTransition(BaseModel):
    status: IntentStage
    evidence_references: list[EvidenceReference] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class IntentJourneyRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    status: str
    evidence_references: list[dict[str, Any]]
    confidence: float


class SalesIntentCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    evidence_references: list[EvidenceReference] = Field(min_length=1)
    intent_type: Literal[
        "research", "comparison", "purchase_intent", "quote_request", "repeat_purchase"
    ]
    confidence: float = Field(ge=0, le=1)
    recommendation: str = Field(min_length=1, max_length=10_000)


class SalesIntentRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    evidence_references: list[dict[str, Any]]
    intent_type: str
    confidence: float
    recommendation: str


class SupportLearningCreate(BaseModel):
    organization_id: UUID
    source_issue_id: UUID
    customer_impact: str = Field(min_length=1, max_length=10_000)
    root_cause_category: Literal[
        "delivery", "quality", "product_usage", "payment", "refund", "expectation", "other"
    ]
    recommendation: str = Field(min_length=1, max_length=10_000)


class SupportLearningRead(ReadModel):
    organization_id: UUID
    source_issue_id: UUID
    customer_impact: str
    root_cause_category: str
    recommendation: str


class JourneyDashboardRead(BaseModel):
    organization_id: UUID
    customer_engagement: dict[str, int]
    intent_distribution: dict[str, int]
    sales_signals: dict[str, int]
    support_trends: dict[str, int]
