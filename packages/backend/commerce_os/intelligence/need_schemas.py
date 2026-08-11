from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class CustomerNeedCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    category: str = Field(min_length=1, max_length=80)
    confidence_score: float = Field(ge=0, le=1)


class CustomerNeedUpdate(BaseModel):
    status: Literal["validated", "archived"]


class CustomerNeedRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    category: str
    confidence_score: float
    status: str


class PainNeedMappingCreate(BaseModel):
    organization_id: UUID
    pain_cluster_id: UUID
    need_id: UUID
    mapping_strength: float = Field(ge=0, le=1)
    evidence_count: int = Field(ge=1)


class PainNeedMappingRead(ReadModel):
    organization_id: UUID
    pain_cluster_id: UUID
    need_id: UUID
    mapping_strength: float
    evidence_count: int


class ProductSolutionCreate(BaseModel):
    organization_id: UUID
    need_id: UUID
    product_category: str = Field(min_length=1, max_length=120)
    solution_description: str = Field(min_length=1, max_length=10_000)
    fit_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1)


class ProductSolutionRead(ReadModel):
    organization_id: UUID
    need_id: UUID
    product_category: str
    solution_description: str
    fit_score: float
    confidence_score: float


class CustomerBackedAssessmentCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    need_id: UUID
    pain_strength: float = Field(ge=0, le=100)
    solution_fit: float = Field(ge=0, le=100)
    intent_score: float = Field(ge=0, le=100)
    competition_score: float = Field(ge=0, le=100)
    margin_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)


class CustomerBackedAssessmentRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    need_id: UUID
    pain_strength: float
    solution_fit: float
    intent_score: float
    competition_score: float
    margin_score: float
    risk_score: float
    overall_score: float
    formula_version: str
