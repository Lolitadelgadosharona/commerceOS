from uuid import UUID

from pydantic import BaseModel, Field


class BusinessDemandSignalCreate(BaseModel):
    organization_id: UUID
    source_domain: str = Field(min_length=1, max_length=40)
    industry: str = Field(min_length=1, max_length=160)
    signal_type: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=20_000)
    evidence_reference: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    source_research_result_id: UUID
