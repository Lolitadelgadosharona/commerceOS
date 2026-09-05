from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class ListingVersionCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=250)
    subtitle: str | None = Field(default=None, max_length=500)
    summary: str = Field(min_length=1, max_length=5000)
    description: str = Field(min_length=1, max_length=20000)
    customer_problem: str | None = None
    solution: str | None = None
    features: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    specifications: dict[str, object] = Field(default_factory=dict)
    use_cases: list[str] = Field(default_factory=list)
    whats_included: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    care_usage: str | None = None
    shipping_facts: str | None = None
    return_facts: str | None = None
    risk_reversal: str | None = None
    seo_title: str | None = Field(default=None, max_length=250)
    meta_description: str | None = Field(default=None, max_length=500)
    slug_suggestion: str | None = Field(default=None, max_length=250)
    primary_topic: str | None = Field(default=None, max_length=250)
    secondary_topics: list[str] = Field(default_factory=list)
    structured_attributes: dict[str, object] = Field(default_factory=dict)
    commercial_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price_status: Literal["unknown", "assumption", "approved"] = "unknown"
    change_reason: str = Field(min_length=1, max_length=5000)


class ListingVersionRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    product_truth_id: UUID
    product_truth_version: int
    listing_version: int
    status: str
    title: str
    subtitle: str | None
    summary: str
    description: str
    customer_problem: str | None
    solution: str | None
    features: list[str]
    benefits: list[str]
    specifications: dict[str, object]
    use_cases: list[str]
    whats_included: list[str]
    warnings: list[str]
    care_usage: str | None
    shipping_facts: str | None
    return_facts: str | None
    risk_reversal: str | None
    seo_title: str | None
    meta_description: str | None
    slug_suggestion: str | None
    primary_topic: str | None
    secondary_topics: list[str]
    structured_attributes: dict[str, object]
    commercial_price: Decimal | None
    currency: str | None
    price_status: str
    change_reason: str
    approval_request_id: UUID | None
    created_by: UUID
    approved_by: UUID | None
    approved_at: datetime | None


class ClaimCreate(BaseModel):
    organization_id: UUID
    claim_text: str = Field(min_length=1, max_length=5000)
    claim_type: Literal[
        "product_fact",
        "feature",
        "benefit",
        "performance",
        "quality",
        "material",
        "dimension",
        "compatibility",
        "shipping",
        "return",
        "compliance",
        "comparative",
        "sustainability",
        "health_or_safety",
        "other",
    ]
    classification: Literal["fact", "derived", "positioning", "assumption"]


class ClaimEvidenceCreate(BaseModel):
    organization_id: UUID
    source_type: Literal[
        "product_truth",
        "build_requirement",
        "supplier_evidence",
        "product_economics",
        "approved_policy",
        "market_evidence",
        "human_positioning",
    ]
    source_reference: str = Field(min_length=1, max_length=500)
    evidence_text: str = Field(min_length=1, max_length=5000)
    classification: Literal["verified", "approved", "observed", "assumption", "unknown"]


class ClaimRead(ReadModel):
    organization_id: UUID
    listing_version_id: UUID
    product_id: UUID
    claim_text: str
    claim_type: str
    classification: str
    support_status: str
    risk_category: str
    review_status: str
    human_review_required: bool
    blocking: bool
    created_by: UUID


class ClaimEvidenceRead(ReadModel):
    organization_id: UUID
    claim_id: UUID
    source_type: str
    source_reference: str
    evidence_text: str
    classification: str


class ClaimReviewDecision(BaseModel):
    organization_id: UUID
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=3, max_length=5000)


class FAQCreate(BaseModel):
    organization_id: UUID
    question: str = Field(min_length=1, max_length=5000)
    answer: str | None = Field(default=None, max_length=10000)
    answer_status: Literal[
        "supported_answer", "needs_review", "missing_product_fact", "missing_policy"
    ]
    evidence_reference: str | None = Field(default=None, max_length=500)


class FAQRead(ReadModel):
    organization_id: UUID
    listing_version_id: UUID
    question: str
    answer: str | None
    answer_status: str
    evidence_reference: str | None


class ReviewRequest(BaseModel):
    organization_id: UUID
    reason: str = Field(min_length=3, max_length=5000)


class ApproveListing(BaseModel):
    organization_id: UUID
    approval_request_id: UUID


class ReadinessItem(BaseModel):
    code: str
    severity: Literal["blocker", "warning"]
    message: str
    references: list[str] = Field(default_factory=list)


class ClaimReviewItem(BaseModel):
    id: UUID
    claim: str
    claim_type: str
    support_status: str
    sources: list[str]
    risk_level: str
    policy_requirement: str | None
    human_review_needed: bool
    blocking: bool


class AllowedFact(BaseModel):
    fact: str
    source: str
    evidence: list[str]
    can_use: bool
    restrictions: list[str]
    notes: str | None


class ListingPackageRead(BaseModel):
    organization_id: UUID
    product_id: UUID
    product_name: str
    product_truth_id: UUID | None
    product_truth_version: int | None
    listing: ListingVersionRead | None
    allowed_facts: list[AllowedFact]
    claim_review: list[ClaimReviewItem]
    faqs: list[FAQRead]
    blockers: list[ReadinessItem]
    warnings: list[ReadinessItem]
    status: Literal["not_ready", "conditional", "ready"]
    product_truth_fresh: bool
    build_status: str
    structured_data_ready: bool
    next_action: str
    origin_opportunity_id: UUID | None
    origin_hypothesis_id: UUID | None


class ShopifyReadinessProjection(BaseModel):
    status: Literal["draft_concept"] = "draft_concept"
    external_id: None = None
    title: str
    description: str
    product_type: str
    vendor: str | None
    price: Decimal | None
    currency: str | None
    seo_title: str | None
    seo_description: str | None
    metafield_candidates: dict[str, object]
    missing_fields: list[str]
    publication_authorized: Literal[False] = False
