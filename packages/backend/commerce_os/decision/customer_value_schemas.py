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
