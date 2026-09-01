from datetime import date, datetime
from decimal import Decimal
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


ProvenanceClassification = Literal[
    "observed",
    "supplier_claimed",
    "quoted",
    "verified",
    "assumption",
    "ai_inference",
    "unknown",
]


class SupplierEvidenceCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    field_name: str = Field(min_length=1, max_length=100)
    value: object | None = None
    classification: ProvenanceClassification
    source: str = Field(min_length=1, max_length=250)
    confidence: float | None = Field(default=None, ge=0, le=1)
    as_of: datetime | None = None
    evidence_reference: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=5000)


class SupplierEvidenceRead(ReadModel):
    organization_id: UUID
    supplier_id: UUID
    field_name: str
    value: object | None
    classification: str
    source: str
    confidence: float | None
    as_of: datetime | None
    evidence_reference: str | None
    notes: str | None


class SupplierQuoteCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    product_id: UUID
    currency: str = Field(min_length=3, max_length=3)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    minimum_order_quantity: int | None = Field(default=None, ge=1)
    price_tiers: list[dict[str, object]] = Field(default_factory=list, max_length=100)
    sample_cost: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    tooling_cost: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    packaging_cost: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    incoterm: str | None = Field(default=None, max_length=30)
    payment_terms: str | None = Field(default=None, max_length=250)
    lead_time: str | None = Field(default=None, max_length=200)
    quote_date: date
    valid_until: date | None = None
    classification: Literal["quoted", "supplier_claimed", "unknown"] = "quoted"
    source: str = Field(min_length=1, max_length=250)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_reference: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=5000)


class SupplierQuoteRead(ReadModel):
    organization_id: UUID
    supplier_id: UUID
    product_id: UUID
    currency: str
    unit_price: Decimal | None
    minimum_order_quantity: int | None
    price_tiers: list[dict[str, object]]
    sample_cost: Decimal | None
    tooling_cost: Decimal | None
    packaging_cost: Decimal | None
    incoterm: str | None
    payment_terms: str | None
    lead_time: str | None
    quote_date: date
    valid_until: date | None
    classification: str
    source: str
    confidence: float | None
    evidence_reference: str | None
    notes: str | None


class QuoteEconomicsLinkCreate(BaseModel):
    organization_id: UUID
    product_economics_id: UUID
    confidence: float | None = Field(default=None, ge=0, le=1)


class SupplierSelectionRequest(BaseModel):
    organization_id: UUID
    product_id: UUID
    role: Literal["primary", "backup", "alternate"]
    reason: str = Field(min_length=1, max_length=5000)
    source_candidate_id: UUID | None = None


class SupplierSelectionExecute(BaseModel):
    organization_id: UUID
    product_id: UUID
    approval_request_id: UUID
    role: Literal["primary", "backup", "alternate"]
    source_candidate_id: UUID | None = None


class ApprovedProductSupplierRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    supplier_id: UUID
    source_candidate_id: UUID | None
    approval_request_id: UUID
    role: str
    status: str
    approved_by: UUID | None
    approved_at: datetime | None


class QualificationDimension(BaseModel):
    dimension: str
    status: Literal["pass", "conditional", "fail", "unknown"]
    evidence: list[str]
    confidence: float | None
    gaps: list[str]
    risk: str | None


class ReadinessItem(BaseModel):
    code: str
    severity: Literal["blocker", "warning", "info"]
    status: Literal["ready", "blocked", "warning", "unknown"]
    message: str
    references: list[str] = Field(default_factory=list)


class SupplierQualificationRead(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    product_id: UUID
    dimensions: list[QualificationDimension]
    readiness: list[ReadinessItem]
    ready: bool
    next_action: str


class SupplierComparisonRow(BaseModel):
    supplier: SupplierProfileRead
    match: ProductSupplierMatchRead | None
    evaluation: SupplierEvaluationRead | None
    quote: SupplierQuoteRead | None
    risks: list[SupplierRiskRead]
    qualification: SupplierQualificationRead


class SupplierComparisonRead(BaseModel):
    organization_id: UUID
    product_id: UUID
    rows: list[SupplierComparisonRow]


class SupplyReadinessRead(BaseModel):
    organization_id: UUID
    product_id: UUID
    ready: bool
    approved_suppliers: list[ApprovedProductSupplierRead]
    items: list[ReadinessItem]
    next_action: str


class SupplierDetailRead(BaseModel):
    supplier: SupplierProfileRead
    products: list[ProductSupplierMatchRead]
    evidence: list[SupplierEvidenceRead]
    quotes: list[SupplierQuoteRead]
    evaluations: list[SupplierEvaluationRead]
    risks: list[SupplierRiskRead]
    approved_relationships: list[ApprovedProductSupplierRead]
    qualifications: list[SupplierQualificationRead]
    next_action: str
