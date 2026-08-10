from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class ListingStrategyCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    target_customer: str = Field(min_length=1, max_length=5000)
    value_proposition: str = Field(min_length=1, max_length=5000)
    positioning: str = Field(min_length=1, max_length=5000)
    differentiation: str = Field(min_length=1, max_length=5000)


class ListingStrategyUpdate(BaseModel):
    status: Literal["approved", "active", "archived"]


class ListingStrategyRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    target_customer: str
    value_proposition: str
    positioning: str
    differentiation: str
    status: str


class CustomerQuestionCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    question: str = Field(min_length=1, max_length=5000)
    question_type: Literal["buying", "trust", "delivery", "quality", "usage", "objection"]
    source_reference: str = Field(min_length=1, max_length=500)
    importance_score: float = Field(ge=0, le=100)


class CustomerQuestionRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    question: str
    question_type: str
    source_reference: str
    importance_score: float


class ProductDiscoveryKnowledgeCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    entity_type: Literal["product", "use_case", "audience", "problem", "solution", "feature"]
    entity_name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=5000)
    relationship: str = Field(min_length=1, max_length=250)
    confidence_score: float = Field(ge=0, le=1)


class ProductDiscoveryKnowledgeRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    entity_type: str
    entity_name: str
    description: str
    relationship: str
    confidence_score: float


class ContentBriefCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    headline_direction: str = Field(min_length=1, max_length=5000)
    key_benefits: list[str] = Field(default_factory=list, max_length=200)
    proof_points: list[str] = Field(default_factory=list, max_length=200)
    objections: list[str] = Field(default_factory=list, max_length=200)
    trust_elements: list[str] = Field(default_factory=list, max_length=200)


class ContentBriefRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    headline_direction: str
    key_benefits: list[str]
    proof_points: list[str]
    objections: list[str]
    trust_elements: list[str]


class ListingEvidenceCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    evidence_type: Literal["customer_quote", "review_insight", "specification", "supplier_evidence"]
    source_reference: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=5000)
    confidence_score: float = Field(ge=0, le=1)


class ListingEvidenceRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    evidence_type: str
    source_reference: str
    content: str
    confidence_score: float
