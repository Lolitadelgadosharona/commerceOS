from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class DemandAggregationCreate(BaseModel):
    organization_id: UUID
    learning_signal_ids: list[UUID] = Field(min_length=1)
    customer_segment: str = Field(min_length=1, max_length=250)
    category: str = Field(min_length=1, max_length=80)


class DemandSignalTransition(BaseModel):
    status: Literal["review", "approved", "rejected"]
    approval_request_id: UUID | None = None


class DemandSignalRead(ReadModel):
    organization_id: UUID
    source_domain: str
    source_reference_id: UUID
    customer_segment: str
    category: str
    problem_statement: str
    customer_language: str
    frequency: int
    confidence: float
    evidence_count: int
    status: str


class DemandSignalEvidenceRead(ReadModel):
    organization_id: UUID
    demand_signal_id: UUID
    source_type: str
    source_id: UUID
    evidence_text: str


class DemandDashboardItem(BaseModel):
    demand_signal_id: UUID
    category: str
    customer_segment: str
    problem_statement: str
    frequency: int
    confidence: float
    evidence_count: int
    source_conversation_ids: list[UUID]


class DemandDashboardRead(BaseModel):
    organization_id: UUID
    draft_signals: int
    signals_in_review: int
    approved_signals: int
    emerging_customer_pains: list[DemandDashboardItem]
