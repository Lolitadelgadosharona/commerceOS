from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

ProductionStatus = Literal["draft", "submitted", "review", "approved", "cancelled"]
WorkType = Literal["storyboard", "image_concept", "video_concept", "copy_draft", "ugc_concept"]
AllowedAIOutput = Literal["analysis", "draft", "candidate", "classification"]


class CreativeProductionRequestCreate(BaseModel):
    organization_id: UUID
    project_id: UUID
    creative_brief_id: UUID
    format: str = Field(min_length=1, max_length=30)
    channel: str = Field(min_length=1, max_length=50)
    audience: str = Field(min_length=1, max_length=10_000)
    objective: str = Field(min_length=1, max_length=10_000)
    approval_request_id: UUID | None = None


class CreativeProductionRequestTransition(BaseModel):
    status: ProductionStatus
    approval_request_id: UUID | None = None


class CreativeProductionRequestRead(ReadModel):
    organization_id: UUID
    project_id: UUID
    creative_brief_id: UUID
    format: str
    channel: str
    audience: str
    objective: str
    status: str
    requested_by: UUID
    approval_state: str
    approval_request_id: UUID | None


class CreativeProductionWorkCreate(BaseModel):
    organization_id: UUID
    production_request_id: UUID
    work_type: WorkType
    title: str = Field(min_length=1, max_length=250)
    content_metadata: dict[str, Any] = Field(default_factory=dict)


class CreativeProductionWorkRead(ReadModel):
    organization_id: UUID
    production_request_id: UUID
    work_type: str
    title: str
    content_metadata: dict[str, Any]
    status: str


class CreativeAIProvenanceCreate(BaseModel):
    organization_id: UUID
    production_request_id: UUID
    production_work_id: UUID
    ai_request_id: UUID
    output_classification: AllowedAIOutput
    output_metadata: dict[str, Any] = Field(default_factory=dict)
    provenance_note: str = Field(min_length=1, max_length=5000)


class CreativeAIProvenanceRead(ReadModel):
    organization_id: UUID
    production_request_id: UUID
    production_work_id: UUID
    ai_request_id: UUID
    output_classification: str
    output_metadata: dict[str, Any]
    provenance_note: str


class ProductionArtifactCreate(BaseModel):
    organization_id: UUID
    production_request_id: UUID
    product_id: UUID
    asset_type: Literal["image", "video", "ugc", "carousel", "text"]
    source: str = Field(min_length=1, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductionArtifactRead(ReadModel):
    organization_id: UUID
    production_request_id: UUID | None
    product_id: UUID
    asset_type: str
    status: str
    source: str
    metadata: dict[str, Any] = Field(validation_alias="asset_metadata")
    approval_status: str
    review_status: str
    quality_score: float | None


class CreativeQualityReviewCreate(BaseModel):
    organization_id: UUID
    asset_id: UUID
    brand_consistency_score: float = Field(ge=0, le=100)
    claim_safety_score: float = Field(ge=0, le=100)
    product_accuracy_score: float = Field(ge=0, le=100)
    channel_suitability_score: float = Field(ge=0, le=100)
    customer_relevance_score: float = Field(ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1, max_length=10_000)


class CreativeQualityReviewRead(ReadModel):
    organization_id: UUID
    asset_id: UUID
    review_type: str
    score: float
    issues: list[str]
    recommendation: str
    brand_consistency_score: float | None
    claim_safety_score: float | None
    product_accuracy_score: float | None
    channel_suitability_score: float | None
    customer_relevance_score: float | None
    review_status: str
    reviewed_by: UUID | None


class ArtifactReviewTransition(BaseModel):
    review_status: Literal["in_review", "approved", "ready_for_distribution", "rejected"]
