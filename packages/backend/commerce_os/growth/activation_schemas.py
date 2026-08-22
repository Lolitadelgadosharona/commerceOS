from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class RevenueExperimentCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=20_000)
    target_segment: str = Field(min_length=1, max_length=20_000)
    offer_type: str = Field(min_length=1, max_length=120)
    message_strategy: str = Field(min_length=1, max_length=20_000)


class RevenueExperimentTransition(BaseModel):
    status: Literal["active", "completed", "archived"]


class RevenueExperimentRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    target_segment: str
    offer_type: str
    message_strategy: str
    status: str
    created_by: UUID


class ProspectAssignmentCreate(BaseModel):
    organization_id: UUID
    experiment_id: UUID
    prospect_id: UUID
    assigned_offer: str = Field(min_length=1, max_length=20_000)
    assigned_message: str = Field(min_length=1, max_length=20_000)


class ProspectAssignmentRead(ReadModel):
    organization_id: UUID
    experiment_id: UUID
    prospect_id: UUID
    assigned_offer: str
    assigned_message: str
    result_status: str


class OutreachEventCreate(BaseModel):
    organization_id: UUID
    prospect_experiment_link_id: UUID
    outreach_draft_id: UUID | None = None
    event_type: Literal[
        "draft_created",
        "approved",
        "sent_manually",
        "reply_received",
        "follow_up_needed",
        "converted",
    ]
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutreachEventRead(ReadModel):
    organization_id: UUID
    prospect_experiment_link_id: UUID
    outreach_draft_id: UUID | None
    event_type: str
    occurred_at: datetime
    recorded_by: UUID
    event_metadata: dict[str, Any]


class ProspectPromotionCreate(BaseModel):
    organization_id: UUID
    email: str | None = Field(default=None, max_length=320)
    social_links: dict[str, str] = Field(default_factory=dict)
