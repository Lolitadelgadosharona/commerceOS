from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from commerce_os.shared.schemas import ReadModel
from pydantic import BaseModel, Field

AccountStatus = Literal["candidate", "active", "watch", "dormant", "closed"]
StrategicTier = Literal["standard", "growth", "strategic", "key"]


class StrategicAccountCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    project_id: UUID | None = None
    account_status: AccountStatus = "candidate"
    relationship_stage: str = Field(min_length=1, max_length=50)
    strategic_tier: StrategicTier = "standard"
    relationship_strength: float = Field(ge=0, le=100)
    commercial_potential: float = Field(ge=0, le=100)
    expansion_potential: float = Field(ge=0, le=100)
    replenishment_potential: float = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    last_meaningful_activity_at: datetime | None = None
    next_review_at: datetime | None = None


class StrategicAccountUpdate(BaseModel):
    account_status: AccountStatus | None = None
    relationship_stage: str | None = Field(default=None, min_length=1, max_length=50)
    strategic_tier: StrategicTier | None = None
    next_review_at: datetime | None = None


class StrategicAccountRead(StrategicAccountCreate, ReadModel):
    pass


class StakeholderCreate(BaseModel):
    organization_id: UUID
    strategic_account_id: UUID
    contact_reference: str = Field(min_length=1, max_length=500)
    role: str = Field(min_length=1, max_length=100)
    decision_influence: float = Field(ge=0, le=100)
    decision_maker: bool = False
    relationship_strength: float = Field(ge=0, le=100)
    evidence_reference: str | None = None


class StakeholderRead(StakeholderCreate, ReadModel):
    pass


class ReplenishmentCreate(BaseModel):
    organization_id: UUID
    strategic_account_id: UUID
    product_reference: str | None = None
    historical_purchase_references: list[str] = Field(default_factory=list)
    purchase_frequency_indicator: float | None = Field(default=None, ge=0, le=100)
    last_purchase_date: date | None = None
    expected_replenishment_cycle_days: int | None = Field(default=None, gt=0)
    behavior_indicators: dict[str, Any] = Field(default_factory=dict)
    conversation_evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    evidence_summary: str | None = None
    status: Literal["draft", "review", "current", "expired"] = "draft"


class ReplenishmentRead(ReplenishmentCreate, ReadModel):
    estimated_next_purchase_start: date | None
    estimated_next_purchase_end: date | None
    replenishment_probability: float | None
    assessment_version: str


class ExpansionCreate(BaseModel):
    organization_id: UUID
    strategic_account_id: UUID
    opportunity_type: Literal[
        "reorder",
        "upsell",
        "cross_sell",
        "b2b_volume_expansion",
        "new_product",
        "new_market",
        "strategic_partnership",
    ]
    product_reference: str | None = None
    estimated_value_indicator: float | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: dict[str, Any] = Field(default_factory=dict)
    risk_indicator: float = Field(ge=0, le=100)
    status: Literal["identified", "review", "ready", "dismissed", "expired"] = "identified"


class ExpansionUpdate(BaseModel):
    status: Literal["identified", "review", "ready", "dismissed", "expired"]


class ExpansionRead(ExpansionCreate, ReadModel):
    pass


class NextBestActionCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    strategic_account_id: UUID | None = None
    recommendation_type: Literal[
        "follow_up",
        "replenishment_check",
        "product_recommendation",
        "cross_sell_review",
        "account_review",
        "human_outreach",
        "no_action",
        "risk_review",
    ]
    reason: str = Field(min_length=1)
    evidence_references: list[str] = Field(default_factory=list)
    priority: Literal["low", "normal", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    recommended_time_window: date | None = None
    human_review_required: bool = True
    status: Literal["draft", "reviewed", "accepted", "rejected"] = "draft"


class NextBestActionRead(NextBestActionCreate, ReadModel):
    formula_or_rule_version: str
    decision_queue_item_id: UUID | None


class StrategicScoreCreate(BaseModel):
    organization_id: UUID
    strategic_account_id: UUID
    input_values: dict[str, float | None]


class StrategicScoreRead(ReadModel):
    organization_id: UUID
    strategic_account_id: UUID
    input_values: dict[str, float | None]
    weights: dict[str, float]
    formula_version: str
    score: float
    confidence: float
    evidence_coverage: float
