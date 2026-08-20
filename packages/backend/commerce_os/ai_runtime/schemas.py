from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel

CapabilityType = Literal[
    "text_generation",
    "image_generation",
    "video_generation",
    "embedding",
    "classification",
    "vision",
    "speech",
]
OutputClassification = Literal["recommendation", "draft", "analysis", "candidate", "classification"]


class ProviderCreate(BaseModel):
    organization_id: UUID
    provider_identity: str = Field(min_length=1, max_length=150)
    display_name: str = Field(min_length=1, max_length=200)
    availability_state: Literal["available", "degraded", "unavailable", "disabled"]
    provider_version: str = Field(min_length=1, max_length=100)
    cost_metadata: dict[str, Any] = Field(default_factory=dict)
    base_url: str | None = Field(default=None, max_length=500)
    credential_reference: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,199}$")
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    runtime_configuration: dict[str, Any] = Field(default_factory=dict)


class ProviderRead(ReadModel, ProviderCreate):
    pass


class CapabilityCreate(BaseModel):
    organization_id: UUID
    provider_id: UUID
    model_identity: str = Field(min_length=1, max_length=200)
    capability_type: CapabilityType
    model_version: str = Field(min_length=1, max_length=100)
    available: bool
    cost_metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityRead(ReadModel, CapabilityCreate):
    pass


class AIRequestCreate(BaseModel):
    organization_id: UUID
    purpose: str = Field(min_length=1, max_length=200)
    context_type: str = Field(min_length=1, max_length=100)
    context_reference: str = Field(min_length=1, max_length=500)
    capability_id: UUID | None = None
    approval_request_id: UUID | None = None


class AIRequestTransition(BaseModel):
    organization_id: UUID
    status: Literal[
        "submitted", "approved_if_required", "ready", "completed", "failed", "cancelled"
    ]
    output_classification: OutputClassification | None = None
    output_metadata: dict[str, Any] = Field(default_factory=dict)
    failure_reason: str | None = Field(default=None, max_length=10_000)


class AIRequestRead(ReadModel):
    organization_id: UUID
    requester_id: UUID
    purpose: str
    context_type: str
    context_reference: str
    capability_id: UUID | None
    approval_request_id: UUID | None
    status: str
    output_classification: str | None
    output_metadata: dict[str, Any]
    failure_reason: str | None
    prompt_version_id: UUID | None
    task_type: str | None
    selected_provider_identity: str | None
    selected_model_identity: str | None
    provider_request_id: str | None
    response_content: dict[str, Any] | None
    structured_output_valid: bool | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: int | None
    retry_count: int
    failure_category: str | None


class AIExecutionSubmit(BaseModel):
    organization_id: UUID
    purpose: str = Field(min_length=1, max_length=200)
    context_type: str = Field(min_length=1, max_length=100)
    context_reference: str = Field(min_length=1, max_length=500)
    capability_id: UUID
    prompt_version_id: UUID | None = None
    task_type: str = Field(min_length=1, max_length=100)
    system_instructions: str = Field(min_length=1, max_length=100_000)
    input_content: str = Field(min_length=1, max_length=200_000)
    output_classification: OutputClassification
    expected_output_schema: dict[str, Any] | None = None
    runtime_configuration: dict[str, Any] = Field(default_factory=dict)
    provenance_context: dict[str, Any] = Field(default_factory=dict)
    approval_request_id: UUID | None = None


class AIExecutionResult(ReadModel):
    organization_id: UUID
    request_id: UUID
    status: str
    output_classification: str | None
    response_content: dict[str, Any] | None
    structured_output_valid: bool | None
    provider_request_id: str | None
    provider: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: int | None
    retry_count: int
    failure_category: str | None
    failure_reason: str | None


class ResearchAnalysisComposition(BaseModel):
    organization_id: UUID
    analysis_type: Literal["customer_pain", "market_insight", "opportunity_brief"]
    confidence: float = Field(ge=0, le=1)
    methodology_version: str = Field(default="governed-ai-runtime-v1", max_length=80)


class PromptPurposeCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=10_000)
    owning_domain: Literal[
        "intelligence",
        "decision",
        "build",
        "growth",
        "operations",
        "finance",
        "learning",
        "governance",
    ]
    status: Literal["draft", "active", "archived"] = "draft"


class PromptPurposeRead(ReadModel, PromptPurposeCreate):
    pass


class PromptTemplateCreate(BaseModel):
    organization_id: UUID
    purpose_id: UUID
    name: str = Field(min_length=1, max_length=200)
    status: Literal["draft", "active", "archived"] = "draft"


class PromptTemplateRead(ReadModel):
    organization_id: UUID
    purpose_id: UUID
    name: str
    owner_id: UUID
    status: str


class PromptVersionCreate(BaseModel):
    organization_id: UUID
    template_id: UUID
    prompt_content: str = Field(min_length=1, max_length=100_000)
    configuration: dict[str, Any] = Field(default_factory=dict)
    status: Literal["draft", "review", "approved", "retired"] = "draft"


class PromptVersionRead(ReadModel):
    organization_id: UUID
    template_id: UUID
    version_number: int
    prompt_content: str
    configuration: dict[str, Any]
    created_by: UUID
    status: str


class PromptEvaluationCreate(BaseModel):
    organization_id: UUID
    prompt_version_id: UUID
    score: float = Field(ge=0, le=100)
    result: Literal["pass", "fail", "needs_review"]
    notes: str = Field(default="", max_length=20_000)


class PromptEvaluationRead(ReadModel):
    organization_id: UUID
    prompt_version_id: UUID
    evaluator_id: UUID
    score: float
    result: str
    notes: str


class CostObservationCreate(BaseModel):
    organization_id: UUID
    provider_id: UUID
    capability_id: UUID
    usage_quantity: Decimal = Field(ge=0, max_digits=19, decimal_places=6)
    usage_unit: str = Field(min_length=1, max_length=50)
    estimated_cost: Decimal = Field(ge=0, max_digits=19, decimal_places=6)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    project_id: UUID | None = None
    related_request_id: UUID | None = None


class CostObservationRead(ReadModel, CostObservationCreate):
    pass
