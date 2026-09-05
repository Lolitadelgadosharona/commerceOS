from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

RequirementStatus = Literal["pass", "conditional", "fail", "unknown"]


class CandidatePromotionCreate(BaseModel):
    organization_id: UUID
    supplier_profile_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=250)
    country: str | None = Field(default=None, min_length=2, max_length=100)


class CandidatePromotionRead(ReadModel):
    organization_id: UUID
    supplier_candidate_id: UUID
    supplier_profile_id: UUID
    confirmed_by: UUID
    confirmed_at: datetime


class ProductBuildRequirementCreate(BaseModel):
    organization_id: UUID
    product_truth_id: UUID
    attribute_key: str = Field(min_length=1, max_length=100)
    display_label: str = Field(min_length=1, max_length=200)
    value: object | None = None
    unit: str | None = Field(default=None, max_length=50)
    classification: Literal["verified", "observed", "supplier_claimed", "assumption", "unknown"]
    evidence_reference: str | None = Field(default=None, max_length=500)
    required_for_build: bool = True
    required_for_listing: bool = False


class ProductBuildRequirementRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    product_truth_id: UUID
    attribute_key: str
    display_label: str
    value: object | None
    unit: str | None
    classification: str
    evidence_reference: str | None
    required_for_build: bool
    required_for_listing: bool


class BuildRequirementPolicyCreate(BaseModel):
    organization_id: UUID
    sample_required: bool = False
    inspection_required: bool = False
    compliance_evidence_required: bool = False
    packaging_validation_required: bool = False
    reason: str = Field(min_length=1, max_length=5000)


class BuildRequirementPolicyRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    sample_required: bool
    inspection_required: bool
    compliance_evidence_required: bool
    packaging_validation_required: bool
    reason: str


class ProductSampleCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    approved_product_supplier_id: UUID | None = None
    sample_identifier: str = Field(min_length=1, max_length=150)
    status: Literal[
        "not_requested", "requested", "received", "under_review", "accepted", "rejected"
    ] = "not_requested"
    requested_at: date | None = None
    received_at: date | None = None
    sample_cost: Decimal | None = Field(default=None, ge=0)
    shipping_cost: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    version_reference: str | None = Field(default=None, max_length=250)
    notes: str | None = Field(default=None, max_length=5000)
    evidence_reference: str | None = Field(default=None, max_length=500)


class ProductSampleRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    supplier_id: UUID
    approved_product_supplier_id: UUID | None
    sample_identifier: str
    status: str
    requested_at: date | None
    received_at: date | None
    sample_cost: Decimal | None
    shipping_cost: Decimal | None
    currency: str | None
    version_reference: str | None
    notes: str | None
    evidence_reference: str | None
    recorded_by: UUID
    review_status: str
    review_dimensions: dict[str, object]
    review_notes: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None


class ProductSampleReview(BaseModel):
    organization_id: UUID
    status: RequirementStatus
    dimensions: dict[str, RequirementStatus] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=5000)


class SupplierValidationCreate(BaseModel):
    organization_id: UUID
    supplier_id: UUID
    sample_id: UUID | None = None
    validation_type: Literal[
        "document",
        "sample_observation",
        "inspection",
        "quality",
        "certification",
        "production_capability",
        "packaging",
        "lead_time",
        "quote_verification",
    ]
    classification: Literal[
        "supplier_claim",
        "documented_evidence",
        "sample_observation",
        "inspection_result",
        "human_verified",
        "unknown",
    ]
    result: RequirementStatus
    observations: str = Field(min_length=1, max_length=5000)
    critical_defects: int | None = Field(default=None, ge=0)
    major_defects: int | None = Field(default=None, ge=0)
    minor_defects: int | None = Field(default=None, ge=0)
    evidence_reference: str | None = Field(default=None, max_length=500)
    observed_at: date | None = None


class SupplierValidationRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    supplier_id: UUID
    sample_id: UUID | None
    validation_type: str
    classification: str
    result: str
    observations: str
    critical_defects: int | None
    major_defects: int | None
    minor_defects: int | None
    evidence_reference: str | None
    verified_by: UUID | None
    observed_at: date | None


class BuildReadinessItem(BaseModel):
    code: str
    severity: Literal["blocker", "warning", "info"]
    message: str
    references: list[str] = Field(default_factory=list)


class SupplierFitItem(BaseModel):
    requirement: str
    required_value: object | None
    supplier_response: object | None
    evidence: list[str]
    status: RequirementStatus
    gap: str | None


class BuildSupplierRelationship(BaseModel):
    id: UUID
    supplier_id: UUID
    approval_request_id: UUID
    role: str
    status: str


class BuildPackageRead(BaseModel):
    organization_id: UUID
    product_id: UUID
    product_name: str
    product_truth_id: UUID | None
    product_truth_version: int | None
    specifications: dict[str, object]
    requirements: list[ProductBuildRequirementRead]
    approved_suppliers: list[UUID]
    supplier_relationships: list[BuildSupplierRelationship]
    supplier_fit: list[SupplierFitItem]
    samples: list[ProductSampleRead]
    validations: list[SupplierValidationRead]
    quote_ids: list[UUID]
    quote_economics_ids: list[UUID]
    blockers: list[BuildReadinessItem]
    warnings: list[BuildReadinessItem]
    status: Literal["not_ready", "conditional", "ready"]
    next_action: str
    origin_opportunity_id: UUID | None
    origin_hypothesis_id: UUID | None
