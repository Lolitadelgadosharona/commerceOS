from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class CustomerValueCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    revenue_indicator: float = Field(ge=0, le=100)
    margin_indicator: float = Field(ge=0, le=100)
    repeat_probability: float = Field(ge=0, le=1)
    strategic_potential: float = Field(ge=0, le=100)
    risk_indicator: float = Field(ge=0, le=100)
    contribution_potential: float | None = Field(default=None, ge=0, le=100)
    risk_indicators: list[str] = Field(default_factory=list, max_length=100)
    confidence: float = Field(default=1.0, ge=0, le=1)


class CustomerValueRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    revenue_indicator: float
    margin_indicator: float
    repeat_probability: float
    strategic_potential: float
    risk_indicator: float
    score: float
    formula_version: str
    contribution_potential: float
    risk_indicators: list[str]
    confidence: float
