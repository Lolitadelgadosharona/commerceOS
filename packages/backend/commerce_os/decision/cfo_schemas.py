from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class CFOInsightCreate(BaseModel):
    organization_id: UUID
    type: Literal["profit_decline", "cac_increase", "refund_spike", "margin_risk"]
    severity: Literal["low", "medium", "high", "critical"]
    finding: str = Field(min_length=1, max_length=10_000)
    impact: str = Field(min_length=1, max_length=10_000)
    recommendation: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)


class CFOInsightRead(ReadModel):
    organization_id: UUID
    type: str
    severity: str
    finding: str
    impact: str
    recommendation: str
    confidence: float
