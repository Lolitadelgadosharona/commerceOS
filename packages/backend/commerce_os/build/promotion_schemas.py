from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.build.schemas import ProductRead, ProductTruthRead
from commerce_os.shared.schemas import ReadModel


class PromotionRequestCreate(BaseModel):
    organization_id: UUID
    brand_id: UUID
    reason: str = Field(min_length=1, max_length=5000)


class BrandOption(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    organization_id: UUID
    name: str
    slug: str


class PromotionExecute(BaseModel):
    organization_id: UUID
    approval_request_id: UUID


class ReadinessItem(BaseModel):
    code: str
    severity: Literal["blocker", "warning", "info"]
    status: Literal["ready", "missing", "blocked", "warning"]
    message: str
    references: list[str] = Field(default_factory=list)


class PromotionReadiness(BaseModel):
    organization_id: UUID
    product_hypothesis_id: UUID
    opportunity_id: UUID
    ready: bool
    items: list[ReadinessItem]


class ProductPromotionRead(ReadModel):
    organization_id: UUID
    product_hypothesis_id: UUID
    opportunity_id: UUID
    brand_id: UUID
    approval_request_id: UUID
    product_id: UUID | None
    requested_by: UUID
    promoted_by: UUID | None
    promoted_at: datetime | None
    status: str


class OriginProductHypothesis(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    name: str
    description: str
    customer_problem: str
    solution_description: str
    target_customer: str
    target_market: str
    status: str
    confidence_score: float


class ProductOrigin(BaseModel):
    product: ProductRead
    promotion: ProductPromotionRead
    hypothesis: OriginProductHypothesis


class ProductTruthDraftCreate(BaseModel):
    organization_id: UUID
    summary: str = Field(min_length=1, max_length=5000)
    features: list[str] = Field(default_factory=list, max_length=200)
    specifications: dict[str, object] = Field(default_factory=dict)
    approved_claims: list[str] = Field(default_factory=list, max_length=200)
    restricted_claims: list[str] = Field(default_factory=list, max_length=200)
    usage_notes: str = Field(min_length=1, max_length=5000)
    change_reason: str = Field(min_length=1, max_length=5000)
    supporting_evidence: list[str] = Field(default_factory=list, max_length=200)


class ProductTruthDraftRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    summary: str
    features: list[str]
    specifications: dict[str, object]
    approved_claims: list[str]
    restricted_claims: list[str]
    usage_notes: str
    change_reason: str
    supporting_evidence: list[str]
    created_by: UUID
    approval_request_id: UUID | None
    truth_id: UUID | None
    status: str


class TruthReviewRequest(BaseModel):
    organization_id: UUID
    reason: str = Field(min_length=1, max_length=5000)


class TruthPublishRequest(BaseModel):
    organization_id: UUID
    approval_request_id: UUID


class TruthComparison(BaseModel):
    hypothesis_id: UUID
    product_id: UUID
    truth: ProductTruthRead | None
    comparable_fields: dict[str, dict[str, object | None]]
    non_comparable_fields: list[str]
