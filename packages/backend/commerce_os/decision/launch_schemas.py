from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class ProductPositioningCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    target_customer: str = Field(min_length=1, max_length=10_000)
    customer_problem: str = Field(min_length=1, max_length=10_000)
    primary_benefit: str = Field(min_length=1, max_length=10_000)
    differentiation: str = Field(min_length=1, max_length=10_000)
    positioning_statement: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)


class ProductPositioningRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    target_customer: str
    customer_problem: str
    primary_benefit: str
    differentiation: str
    positioning_statement: str
    confidence: float


class OfferStrategyCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    pricing_hypothesis: str = Field(min_length=1, max_length=10_000)
    bundle_strategy: str = Field(min_length=1, max_length=10_000)
    guarantee_strategy: str = Field(min_length=1, max_length=10_000)
    bonus_strategy: str = Field(min_length=1, max_length=10_000)
    urgency_strategy: str = Field(min_length=1, max_length=10_000)
    confidence: float = Field(ge=0, le=1)


class OfferStrategyRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    pricing_hypothesis: str
    bundle_strategy: str
    guarantee_strategy: str
    bonus_strategy: str
    urgency_strategy: str
    confidence: float


class ProductObjectionCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    objection_type: str = Field(min_length=1, max_length=80)
    customer_language: str = Field(min_length=1, max_length=10_000)
    recommended_response: str = Field(min_length=1, max_length=10_000)
    evidence_reference: str = Field(min_length=1, max_length=500)


class ProductObjectionRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    objection_type: str
    customer_language: str
    recommended_response: str
    evidence_reference: str


class LaunchPackageCreate(BaseModel):
    organization_id: UUID
    product_id: UUID


class LaunchPackageRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    positioning_status: str
    offer_status: str
    objection_status: str
    creative_readiness: str
    listing_readiness: str
    launch_score: float
