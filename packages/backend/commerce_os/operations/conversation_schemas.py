from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

Channel = Literal[
    "website", "email", "instagram", "facebook", "tiktok", "whatsapp", "reddit", "other"
]
Priority = Literal["low", "normal", "high", "urgent"]


class ThreadCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID | None = None
    channel: Channel
    priority: Priority = "normal"
    assigned_role_id: UUID | None = None


class ThreadUpdate(BaseModel):
    status: Literal["open", "waiting", "resolved", "escalated", "archived"]


class ThreadRead(ReadModel):
    organization_id: UUID
    customer_id: UUID | None
    channel: str
    status: str
    priority: str
    assigned_role_id: UUID | None


class MessageCreate(BaseModel):
    organization_id: UUID
    thread_id: UUID
    direction: Literal["inbound", "outbound"]
    sender_type: Literal["customer", "human", "system", "ai"]
    content: str = Field(min_length=1, max_length=100_000)


class MessageRead(ReadModel):
    organization_id: UUID
    thread_id: UUID
    sequence: int
    direction: str
    sender_type: str
    content: str


class IntentCreate(BaseModel):
    organization_id: UUID
    message_id: UUID
    intent_type: Literal[
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
    confidence: float = Field(ge=0, le=1)


class IntentRead(ReadModel):
    organization_id: UUID
    message_id: UUID
    intent_type: str
    confidence: float


class EmotionCreate(BaseModel):
    organization_id: UUID
    message_id: UUID
    emotion: Literal["positive", "neutral", "confused", "frustrated", "angry"]
    confidence: float = Field(ge=0, le=1)


class EmotionRead(ReadModel):
    organization_id: UUID
    message_id: UUID
    emotion: str
    confidence: float


class HandoffCreate(BaseModel):
    organization_id: UUID
    thread_id: UUID
    reason: Literal[
        "high_value_customer",
        "angry_customer",
        "complex_negotiation",
        "policy_exception",
        "ai_uncertain",
    ]
    priority: Priority
    assigned_user_id: UUID | None = None


class HandoffUpdate(BaseModel):
    status: Literal["assigned", "resolved", "cancelled"]
    assigned_user_id: UUID | None = None


class HandoffRead(ReadModel):
    organization_id: UUID
    thread_id: UUID
    reason: str
    priority: str
    status: str
    assigned_user_id: UUID | None
    resolved_at: datetime | None


class KnowledgeCreate(BaseModel):
    organization_id: UUID
    thread_id: UUID
    reference_type: Literal["product_truth", "product_knowledge", "claim_policy", "faq"]
    reference_id: UUID


class KnowledgeRead(ReadModel):
    organization_id: UUID
    thread_id: UUID
    reference_type: str
    reference_id: UUID
