from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

ConnectorType = Literal["reddit", "amazon", "etsy", "search_trend", "news", "social"]


class ConnectorCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=160)
    platform: str = Field(min_length=1, max_length=80)
    connector_type: ConnectorType
    configuration_schema: dict[str, Any]


class ConnectorUpdate(BaseModel):
    status: Literal["active", "inactive", "archived"]


class ConnectorRead(ReadModel):
    organization_id: UUID
    name: str
    platform: str
    connector_type: str
    status: str
    configuration_schema: dict[str, Any]


class MarketDataRecordCreate(BaseModel):
    organization_id: UUID
    source_id: UUID
    external_reference: str = Field(min_length=1, max_length=500)
    content_type: str = Field(min_length=1, max_length=80)
    raw_content: str = Field(min_length=1, max_length=100_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime


class MarketDataRecordRead(ReadModel):
    organization_id: UUID
    source_id: UUID
    external_reference: str
    content_type: str
    raw_content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    captured_at: datetime


class NormalizedMarketItemCreate(BaseModel):
    organization_id: UUID
    source_record_id: UUID
    category: str = Field(min_length=1, max_length=150)
    topic: str = Field(min_length=1, max_length=200)
    customer_language: str = Field(min_length=1, max_length=10_000)
    signal_type: str = Field(min_length=1, max_length=80)
    confidence: float = Field(ge=0, le=1)


class NormalizedMarketItemRead(ReadModel):
    organization_id: UUID
    source_record_id: UUID
    category: str
    topic: str
    customer_language: str
    signal_type: str
    confidence: float


class IngestionJobCreate(BaseModel):
    organization_id: UUID
    source_id: UUID


class IngestionJobUpdate(BaseModel):
    status: Literal["running", "completed", "failed"]
    record_count: int | None = Field(default=None, ge=0)


class IngestionJobRead(ReadModel):
    organization_id: UUID
    source_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    record_count: int
