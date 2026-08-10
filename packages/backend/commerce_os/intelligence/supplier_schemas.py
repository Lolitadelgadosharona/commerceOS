from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

RiskLevel = Literal["low", "medium", "high", "critical"]


class SupplierProfileCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=250)
    source_type: Literal[
        "manual", "manufacturer", "wholesaler", "distributor", "marketplace_reference"
    ]
    country: str = Field(min_length=2, max_length=100)
    capabilities: list[str] = Field(default_factory=list, max_length=200)
    certifications: list[str] = Field(default_factory=list, max_length=200)


class SupplierProfileUpdate(BaseModel):
    status: Literal["evaluating", "approved", "rejected", "archived"]


class SupplierProfileRead(ReadModel):
    organization_id: UUID
    name: str
    source_type: str
    country: str
    capabilities: list[str]
    certifications: list[str]
    status: str


class SupplierEvaluationCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    quality_score: float = Field(ge=0, le=100)
    price_score: float = Field(ge=0, le=100)
    lead_time_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    compliance_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1)


class SupplierEvaluationRead(ReadModel):
    organization_id: UUID
    supplier_id: UUID
    quality_score: float
    price_score: float
    lead_time_score: float
    communication_score: float
    compliance_score: float
    overall_score: float
    confidence_score: float
    formula_version: str


class SupplierRiskCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    risk_type: Literal[
        "quality", "delivery", "compliance", "counterfeit", "capacity", "communication"
    ]
    severity: RiskLevel
    description: str = Field(min_length=1, max_length=5000)
    status: Literal["open", "mitigated", "accepted", "dismissed"] = "open"


class SupplierRiskRead(ReadModel):
    organization_id: UUID
    supplier_id: UUID
    risk_type: str
    severity: str
    description: str
    status: str


class ProductSupplierMatchCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    supplier_id: UUID
    match_score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=5000)


class ProductSupplierMatchRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    supplier_id: UUID
    match_score: float
    recommended: bool
    reason: str


class SupplierDecisionCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    selected_supplier_id: UUID
    decision_reason: str = Field(min_length=1, max_length=5000)
    evidence_reference: str = Field(min_length=1, max_length=500)


class SupplierDecisionRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    selected_supplier_id: UUID
    decision_reason: str
    evidence_reference: str
