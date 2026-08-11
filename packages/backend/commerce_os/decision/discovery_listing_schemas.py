from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class ListingBlueprintCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    title_strategy: str = Field(min_length=1, max_length=10_000)
    benefit_structure: list[str] = Field(min_length=1, max_length=100)
    feature_structure: list[str] = Field(min_length=1, max_length=100)
    faq_structure: list[str] = Field(min_length=1, max_length=100)
    trust_elements: list[str] = Field(min_length=1, max_length=100)
    comparison_points: list[str] = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)


class ListingBlueprintRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    title_strategy: str
    benefit_structure: list[str]
    feature_structure: list[str]
    faq_structure: list[str]
    trust_elements: list[str]
    comparison_points: list[str]
    confidence: float


class GeoKnowledgeAssetCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    entity_description: str = Field(min_length=1, max_length=10_000)
    attributes: dict[str, Any] = Field(min_length=1, max_length=100)
    use_cases: list[str] = Field(min_length=1, max_length=100)
    customer_questions: list[str] = Field(min_length=1, max_length=100)
    answer_structure: dict[str, Any] = Field(min_length=1, max_length=100)
    evidence_reference: str = Field(min_length=1, max_length=500)


class GeoKnowledgeAssetRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    entity_description: str
    attributes: dict[str, Any]
    use_cases: list[str]
    customer_questions: list[str]
    answer_structure: dict[str, Any]
    evidence_reference: str


class ListingAssessmentCreate(BaseModel):
    organization_id: UUID
    product_id: UUID


class ListingQualityRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    truth_score: float
    customer_language_score: float
    geo_score: float
    trust_score: float
    conversion_score: float
    overall_score: float


class AIDiscoveryReadinessRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    coverage_score: float
    missing_information: list[str]
    recommendation: str
