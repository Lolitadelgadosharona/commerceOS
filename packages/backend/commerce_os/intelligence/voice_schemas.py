from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class PainScoreInputs(BaseModel):
    frequency: float = Field(ge=0, le=100)
    emotion: float = Field(ge=0, le=100)
    urgency: float = Field(ge=0, le=100)
    growth: float = Field(ge=0, le=100)


class PainClusterCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=10_000)
    confidence_score: float = Field(ge=0, le=1)
    score_inputs: PainScoreInputs


class PainClusterUpdate(BaseModel):
    status: Literal["active", "archived"]


class PainClusterRead(ReadModel):
    organization_id: UUID
    name: str
    category: str
    description: str
    severity_score: float
    confidence_score: float
    status: str
    scoring_evidence: dict[str, Any]


class PainMembershipCreate(BaseModel):
    organization_id: UUID
    pain_candidate_id: UUID
    relevance_score: float = Field(ge=0, le=1)


class PainMembershipRead(ReadModel):
    organization_id: UUID
    cluster_id: UUID
    pain_candidate_id: UUID
    relevance_score: float


class CustomerLanguageCreate(BaseModel):
    organization_id: UUID
    cluster_id: UUID
    phrase: str = Field(min_length=1, max_length=10_000)
    context: str = Field(min_length=1, max_length=10_000)
    usage_type: Literal["listing", "creative", "sales", "support", "product"]
    frequency: int = Field(ge=0)


class CustomerLanguageRead(ReadModel):
    organization_id: UUID
    cluster_id: UUID
    phrase: str
    context: str
    usage_type: str
    frequency: int


class IntentScoreInputs(BaseModel):
    question_behavior: float = Field(ge=0, le=100)
    solution_seeking: float = Field(ge=0, le=100)
    purchase_language: float = Field(ge=0, le=100)


class PurchaseIntentCreate(BaseModel):
    organization_id: UUID
    source_record_id: UUID
    intent_type: Literal["research", "comparison", "buying_intent", "urgent_need"]
    confidence_score: float = Field(ge=0, le=1)
    evidence: dict[str, Any]
    score_inputs: IntentScoreInputs


class PurchaseIntentRead(ReadModel):
    organization_id: UUID
    source_record_id: UUID
    intent_type: str
    confidence_score: float
    evidence: dict[str, Any]
    intent_score: float
