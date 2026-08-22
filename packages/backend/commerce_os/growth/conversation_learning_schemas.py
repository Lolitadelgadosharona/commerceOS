from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

ObjectionType = Literal[
    "price", "timing", "trust", "existing_supplier", "no_need", "wrong_contact", "other"
]


class ConversationAnalysisTransition(BaseModel):
    status: Literal["reviewed", "accepted", "rejected"]


class ObjectionRecordCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    customer_segment: str = Field(min_length=1, max_length=250)
    objection_type: ObjectionType
    outcome: Literal["pending", "resolved", "unresolved", "lost", "converted"] = "pending"


class ObjectionRecordRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    prospect_id: UUID
    objection_type: str
    customer_segment: str
    original_message: str
    suggested_response: str
    outcome: str


class SalesLearningSignalCreate(BaseModel):
    organization_id: UUID
    analysis_id: UUID
    objection_record_id: UUID | None = None
    signal_type: Literal[
        "objection_pattern", "buying_signal", "message_response", "lost_reason", "segment_signal"
    ]
    insight: str = Field(min_length=1, max_length=20_000)
    future_recommendation: str = Field(min_length=1, max_length=20_000)
    confidence: float = Field(ge=0, le=1)


class SalesLearningSignalRead(ReadModel):
    organization_id: UUID
    analysis_id: UUID
    objection_record_id: UUID | None
    learning_observation_id: UUID
    signal_type: str
    insight: str
    future_recommendation: str
    confidence: float


class MessagePerformanceCreate(BaseModel):
    organization_id: UUID
    outreach_draft_id: UUID
    prospect_experiment_link_id: UUID | None = None
    customer_segment: str = Field(min_length=1, max_length=250)
    message_strategy: str = Field(min_length=1, max_length=20_000)
    outcome: Literal["sent", "replied", "positive", "negative", "converted", "lost"]
    observed_at: datetime
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessagePerformanceRead(ReadModel):
    organization_id: UUID
    outreach_draft_id: UUID
    prospect_experiment_link_id: UUID | None
    customer_segment: str
    message_strategy: str
    outcome: str
    observed_at: datetime
    confidence: float
    observation_metadata: dict[str, Any]


class ObjectionMetric(BaseModel):
    objection_type: str
    count: int


class MessageMetric(BaseModel):
    message_strategy: str
    observations: int
    positive_or_converted: int


class SegmentMetric(BaseModel):
    customer_segment: str
    observations: int
    replies: int
    positive_or_converted: int


class SalesKnowledgeDashboardRead(BaseModel):
    organization_id: UUID
    total_conversations: int
    reply_rate: float | None
    positive_signals: int
    most_common_objections: list[ObjectionMetric]
    best_performing_messages: list[MessageMetric]
    lost_reasons: list[ObjectionMetric]
    segment_performance: list[SegmentMetric]
