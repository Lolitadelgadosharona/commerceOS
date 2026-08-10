from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class ProductCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=5000)
    category: str = Field(min_length=1, max_length=150)
    brand_id: UUID


class ProductUpdate(BaseModel):
    status: Literal["active", "archived"]


class ProductRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    category: str
    brand_id: UUID
    status: str


class ProductApprovalRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=5000)


class ProductTruthCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    approval_id: UUID
    summary: str = Field(min_length=1, max_length=5000)
    features: list[str] = Field(default_factory=list, max_length=200)
    specifications: dict[str, object] = Field(default_factory=dict)
    approved_claims: list[str] = Field(default_factory=list, max_length=200)
    restricted_claims: list[str] = Field(default_factory=list, max_length=200)
    usage_notes: str = Field(min_length=1, max_length=5000)


class ProductTruthRead(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    organization_id: UUID
    product_id: UUID
    version: int
    summary: str
    features: list[str]
    specifications: dict[str, object]
    approved_claims: list[str]
    restricted_claims: list[str]
    usage_notes: str
    created_by: UUID
    approval_id: UUID
    created_at: datetime
    updated_at: datetime


class ProductKnowledgeItemUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0, le=1)
    approval_status: Literal["draft", "approved", "rejected"]


class ProductKnowledgeItemCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    type: Literal["feature", "faq", "objection", "limitation", "use_case", "care_instruction"]
    content: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0, le=1)
    approval_status: Literal["draft", "approved", "rejected"] = "draft"


class ProductKnowledgeItemRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    type: str
    content: str
    confidence: float
    approval_status: str


class ProductClaimPolicyCreate(BaseModel):
    organization_id: UUID
    brand_id: UUID
    claim_type: str = Field(min_length=1, max_length=100)
    allowed: bool
    reason: str = Field(min_length=1, max_length=5000)
    evidence_required: bool


class ProductClaimPolicyRead(ReadModel):
    organization_id: UUID
    brand_id: UUID
    claim_type: str
    allowed: bool
    reason: str
    evidence_required: bool
