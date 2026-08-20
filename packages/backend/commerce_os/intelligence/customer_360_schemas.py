from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class JourneyEventCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    identity_link_id: UUID | None = None
    event_type: Literal[
        "content_viewed",
        "clicked",
        "conversation_started",
        "purchase_reference",
        "support_request",
        "refund_reference",
        "ad_interaction",
        "page_view",
        "product_interaction",
        "question_received",
        "purchase_intent",
        "quote_requested",
    ]
    source: str = Field(min_length=1, max_length=200)
    reference_id: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict, max_length=200)
    occurred_at: datetime
    confidence: float = Field(default=1.0, ge=0, le=1)


class JourneyEventRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    identity_link_id: UUID | None
    event_type: str
    source: str
    reference_id: str
    metadata: dict[str, Any] = Field(validation_alias="event_metadata")
    occurred_at: datetime
    confidence: float


class Customer360Read(ReadModel):
    organization_id: UUID
    customer_id: UUID
    identity_count: int
    conversation_count: int
    journey_summary: dict[str, Any]
    risk_summary: dict[str, Any]
    value_summary: dict[str, Any]
    last_activity_at: datetime | None
