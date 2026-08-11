from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.intelligence.commercial_risk_models import ProductRiskType
from commerce_os.shared.schemas import ReadModel

Severity = Literal["low", "medium", "high", "critical"]
RiskStatus = Literal["mitigated", "accepted", "dismissed"]


class ProductRiskSignalCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    risk_type: ProductRiskType
    severity: Severity
    evidence: dict[str, Any]
    confidence: float = Field(ge=0, le=1)


class ProductRiskSignalUpdate(BaseModel):
    status: RiskStatus


class ProductRiskSignalRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    risk_type: str
    severity: str
    evidence: dict[str, Any]
    confidence: float
    status: str


class ProductRiskAssessmentCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID


class ProductRiskAssessmentRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    risk_score: float
    risk_level: str
    formula_version: str
    assessment_inputs: dict[str, Any]
    confidence: float


class CommercialViabilityCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    opportunity_score: float = Field(ge=0, le=100)


class CommercialViabilityRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    opportunity_score: float
    risk_score: float
    adjusted_score: float
    recommendation: str
    reasoning: str
