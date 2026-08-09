from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventActor(BaseModel):
    actor_type: str = Field(min_length=1, max_length=50)
    actor_id: str = Field(min_length=1, max_length=200)


class BusinessEventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: EventActor
    source: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=255)
    correlation_id: UUID
    causation_id: UUID | None = None
    organization_id: UUID
    project_id: UUID | None = None
    product_id: UUID | None = None
    customer_id: UUID | None = None
    schema_version: int = Field(default=1, ge=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value
