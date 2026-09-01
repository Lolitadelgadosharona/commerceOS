from typing import Annotated
from uuid import UUID

from commerce_os.build.errors import BuildNotFoundError
from commerce_os.build.models import Product, ProductTruth
from commerce_os.build.promotion_models import ProductPromotion, ProductTruthDraft
from commerce_os.build.promotion_schemas import (
    BrandOption,
    ProductOrigin,
    ProductPromotionRead,
    ProductTruthDraftCreate,
    ProductTruthDraftRead,
    PromotionExecute,
    PromotionReadiness,
    PromotionRequestCreate,
    ReadinessItem,
    TruthComparison,
    TruthPublishRequest,
    TruthReviewRequest,
)
from commerce_os.build.schemas import ProductTruthCreate
from commerce_os.build.services import ProductTruthService, get_scoped_product
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    PrincipalType,
    User,
)
from commerce_os.intelligence.opportunity_models import MarketOpportunity, OpportunityEvidence
from commerce_os.intelligence.product_models import (
    ProductEconomicInputProvenance,
    ProductEconomics,
    ProductHypothesis,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.operations.models import Brand
from commerce_os.shared.database import get_session
from commerce_os.shared.models import utc_now
from commerce_os.shared.scope import reference_belongs_to_organization
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
CRITICAL_METRICS = {
    "selling_price",
    "estimated_product_cost",
    "estimated_shipping_cost",
    "payment_cost",
    "estimated_marketing_cost",
}


def actor_id(request: Request) -> UUID:
    actor = getattr(request.state, "actor", None)
    if actor is not None:
        return UUID(str(actor.id))
    raw = request.headers.get("X-Actor-ID")
    if raw is None:
        raise ApiError(401, "actor_required", "Authenticated actor context is required.")
    return UUID(raw)


def scoped_hypothesis(
    session: Session, hypothesis_id: UUID, organization_id: UUID
) -> ProductHypothesis:
    entity = session.get(ProductHypothesis, hypothesis_id)
    if entity is None or entity.organization_id != organization_id:
        raise ApiError(404, "not_found", "Product Hypothesis was not found.")
    return entity


@router.get("/product-promotion-brands", response_model=list[BrandOption])
def promotion_brands(organization_id: UUID, session: SessionDependency) -> list[Brand]:
    return list(
        session.scalars(
            select(Brand).where(Brand.organization_id == organization_id).order_by(Brand.name)
        )
    )


@router.get("/product-promotions", response_model=list[ProductPromotionRead])
def list_product_promotions(
    organization_id: UUID, session: SessionDependency
) -> list[ProductPromotion]:
    return list(
        session.scalars(
            select(ProductPromotion)
            .where(ProductPromotion.organization_id == organization_id)
            .order_by(ProductPromotion.created_at.desc())
        )
    )


def promotion_readiness(session: Session, hypothesis: ProductHypothesis) -> PromotionReadiness:
    organization_id = hypothesis.organization_id
    opportunity_id = hypothesis.opportunity_id
    items: list[ReadinessItem] = []
    investment = session.scalar(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.object_type == "market_opportunity",
            ApprovalRequest.object_id == opportunity_id,
            ApprovalRequest.requested_action == "approve_investment",
            ApprovalRequest.status == ApprovalStatus.APPROVED,
        )
        .order_by(ApprovalRequest.decision_time.desc())
    )
    items.append(
        ReadinessItem(
            code="investment_approval",
            severity="blocker",
            status="ready" if investment else "blocked",
            message=(
                "Opportunity investment approval is recorded."
                if investment
                else "Opportunity investment approval is required before product promotion."
            ),
            references=[str(investment.id)] if investment else [],
        )
    )
    economics = session.scalar(
        select(ProductEconomics).where(
            ProductEconomics.organization_id == organization_id,
            ProductEconomics.product_id == hypothesis.id,
        )
    )
    inputs = (
        list(
            session.scalars(
                select(ProductEconomicInputProvenance).where(
                    ProductEconomicInputProvenance.organization_id == organization_id,
                    ProductEconomicInputProvenance.product_economics_id == economics.id,
                )
            )
        )
        if economics
        else []
    )
    by_metric = {item.metric: item for item in inputs}
    unknown = sorted(
        metric
        for metric in CRITICAL_METRICS
        if metric not in by_metric or by_metric[metric].classification == "unknown"
    )
    legacy = sorted(
        metric
        for metric, value in by_metric.items()
        if metric in CRITICAL_METRICS and value.classification == "legacy_unprovenanced"
    )
    items.append(
        ReadinessItem(
            code="critical_economics",
            severity="blocker",
            status="blocked" if unknown else "ready",
            message=(
                "Critical economic inputs are UNKNOWN: " + ", ".join(unknown)
                if unknown
                else "Critical economic inputs have numeric values."
            ),
            references=[str(value.id) for value in inputs],
        )
    )
    if legacy:
        items.append(
            ReadinessItem(
                code="legacy_economics_provenance",
                severity="warning",
                status="warning",
                message=(
                    "Economic value exists but source provenance is not established: "
                    + ", ".join(legacy)
                ),
                references=[str(by_metric[metric].id) for metric in legacy],
            )
        )
    critical_risks = list(
        session.scalars(
            select(ProductRisk).where(
                ProductRisk.organization_id == organization_id,
                ProductRisk.product_id == hypothesis.id,
                ProductRisk.severity == "critical",
                ProductRisk.status == "open",
            )
        )
    )
    items.append(
        ReadinessItem(
            code="critical_product_risk",
            severity="blocker",
            status="blocked" if critical_risks else "ready",
            message=(
                "Critical Product Risks remain unresolved."
                if critical_risks
                else "No unresolved critical Product Risk is recorded."
            ),
            references=[str(value.id) for value in critical_risks],
        )
    )
    evidence = list(
        session.scalars(
            select(OpportunityEvidence).where(
                OpportunityEvidence.organization_id == organization_id,
                OpportunityEvidence.opportunity_id == opportunity_id,
            )
        )
    )
    items.append(
        ReadinessItem(
            code="customer_problem_evidence",
            severity="warning",
            status="ready" if evidence else "warning",
            message=(
                "Opportunity evidence supports the customer problem."
                if evidence
                else (
                    "No direct Opportunity evidence is linked; promotion may need stronger support."
                )
            ),
            references=[str(value.id) for value in evidence],
        )
    )
    suppliers = list(
        session.scalars(
            select(SupplierCandidate).where(
                SupplierCandidate.organization_id == organization_id,
                SupplierCandidate.product_id == hypothesis.id,
            )
        )
    )
    items.append(
        ReadinessItem(
            code="supplier_assumptions",
            severity="warning",
            status="ready" if suppliers else "warning",
            message=(
                "Supplier candidates are recorded as intelligence only."
                if suppliers
                else "Supplier work has not started; this does not approve a supplier."
            ),
            references=[str(value.id) for value in suppliers],
        )
    )
    return PromotionReadiness(
        organization_id=organization_id,
        product_hypothesis_id=hypothesis.id,
        opportunity_id=opportunity_id,
        ready=not any(item.severity == "blocker" and item.status != "ready" for item in items),
        items=items,
    )


@router.get(
    "/product-hypotheses/{hypothesis_id}/promotion-readiness",
    response_model=PromotionReadiness,
)
def get_promotion_readiness(
    hypothesis_id: UUID, organization_id: UUID, session: SessionDependency
) -> PromotionReadiness:
    return promotion_readiness(session, scoped_hypothesis(session, hypothesis_id, organization_id))


@router.get(
    "/product-hypotheses/{hypothesis_id}/promotion",
    response_model=ProductPromotionRead | None,
)
def get_promotion(
    hypothesis_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProductPromotion | None:
    scoped_hypothesis(session, hypothesis_id, organization_id)
    return session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == organization_id,
            ProductPromotion.product_hypothesis_id == hypothesis_id,
        )
    )


@router.post(
    "/product-hypotheses/{hypothesis_id}/promotion-request",
    response_model=ProductPromotionRead,
    status_code=201,
)
def request_promotion(
    hypothesis_id: UUID,
    payload: PromotionRequestCreate,
    request: Request,
    session: SessionDependency,
) -> ProductPromotion:
    hypothesis = scoped_hypothesis(session, hypothesis_id, payload.organization_id)
    existing = session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == payload.organization_id,
            ProductPromotion.product_hypothesis_id == hypothesis.id,
        )
    )
    if existing:
        return existing
    state = promotion_readiness(session, hypothesis)
    if not state.ready:
        raise ApiError(409, "promotion_not_ready", "Product promotion blockers remain.")
    if not reference_belongs_to_organization(
        session,
        table_name="brands",
        reference_id=payload.brand_id,
        organization_id=payload.organization_id,
    ):
        raise ApiError(404, "brand_not_found", "Brand was not found in this organization.")
    actor = actor_id(request)
    approval = ApprovalWorkflowService(session).request(
        organization_id=payload.organization_id,
        project_id=None,
        requester_id=actor,
        object_type="product_hypothesis",
        object_id=hypothesis.id,
        requested_action="product.promote",
        reason=payload.reason,
    )
    promotion = ProductPromotion(
        organization_id=payload.organization_id,
        product_hypothesis_id=hypothesis.id,
        opportunity_id=hypothesis.opportunity_id,
        brand_id=payload.brand_id,
        approval_request_id=approval.id,
        requested_by=actor,
        status="pending",
    )
    queue = DecisionQueueItem(
        organization_id=payload.organization_id,
        title=f"Product promotion: {hypothesis.name}",
        domain="governance",
        reason=payload.reason,
        priority="high",
        required_action="approve",
        status="pending",
        approval_request_id=approval.id,
    )
    session.add_all([promotion, queue])
    session.commit()
    session.refresh(promotion)
    return promotion


@router.post(
    "/product-hypotheses/{hypothesis_id}/promote",
    response_model=ProductPromotionRead,
)
def promote(
    hypothesis_id: UUID,
    payload: PromotionExecute,
    request: Request,
    session: SessionDependency,
) -> ProductPromotion:
    hypothesis = scoped_hypothesis(session, hypothesis_id, payload.organization_id)
    promotion = session.scalar(
        select(ProductPromotion)
        .where(
            ProductPromotion.organization_id == payload.organization_id,
            ProductPromotion.product_hypothesis_id == hypothesis.id,
        )
        .with_for_update()
    )
    if promotion is None or promotion.approval_request_id != payload.approval_request_id:
        raise ApiError(409, "promotion_request_required", "Promotion request was not found.")
    if promotion.product_id is not None:
        return promotion
    approval = session.get(ApprovalRequest, promotion.approval_request_id)
    if (
        approval is None
        or approval.status != ApprovalStatus.APPROVED
        or approval.requested_action != "product.promote"
        or approval.object_id != hypothesis.id
    ):
        raise ApiError(409, "promotion_approval_required", "Approved promotion is required.")
    if not promotion_readiness(session, hypothesis).ready:
        raise ApiError(409, "promotion_not_ready", "Product promotion blockers remain.")
    actor = actor_id(request)
    user = session.get(User, actor)
    if user is None or user.organization_id != payload.organization_id:
        raise ApiError(403, "wrong_organization", "Actor is outside this organization.")
    opportunity = session.get(MarketOpportunity, hypothesis.opportunity_id)
    if opportunity is None or opportunity.organization_id != payload.organization_id:
        raise ApiError(409, "opportunity_missing", "Source Opportunity is unavailable.")
    product = Product(
        organization_id=payload.organization_id,
        name=hypothesis.name,
        description=hypothesis.solution_description,
        category=opportunity.category,
        brand_id=promotion.brand_id,
        status="draft",
    )
    session.add(product)
    session.flush()
    promotion.product_id = product.id
    promotion.promoted_by = actor
    promotion.promoted_at = utc_now()
    promotion.status = "promoted"
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type=str(user.principal_type),
        actor_id=actor,
        action="product.promoted",
        entity_type="product",
        entity_id=product.id,
        metadata={
            "product_hypothesis_id": str(hypothesis.id),
            "opportunity_id": str(hypothesis.opportunity_id),
            "approval_request_id": str(approval.id),
        },
    )
    session.commit()
    session.refresh(promotion)
    return promotion


@router.get("/products/{product_id}/origin", response_model=ProductOrigin)
def product_origin(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProductOrigin:
    product = get_scoped_product(session, product_id, organization_id)
    promotion = session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == organization_id,
            ProductPromotion.product_id == product.id,
        )
    )
    if promotion is None:
        raise ApiError(404, "origin_not_found", "Product has no canonical promotion origin.")
    hypothesis = scoped_hypothesis(session, promotion.product_hypothesis_id, organization_id)
    return ProductOrigin(product=product, promotion=promotion, hypothesis=hypothesis)


@router.post(
    "/products/{product_id}/product-truth-drafts",
    response_model=ProductTruthDraftRead,
    status_code=201,
)
def create_truth_draft(
    product_id: UUID,
    payload: ProductTruthDraftCreate,
    request: Request,
    session: SessionDependency,
) -> ProductTruthDraft:
    get_scoped_product(session, product_id, payload.organization_id)
    draft = ProductTruthDraft(
        **payload.model_dump(), product_id=product_id, created_by=actor_id(request), status="draft"
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


@router.get(
    "/products/{product_id}/product-truth-drafts",
    response_model=list[ProductTruthDraftRead],
)
def list_truth_drafts(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> list[ProductTruthDraft]:
    get_scoped_product(session, product_id, organization_id)
    return list(
        session.scalars(
            select(ProductTruthDraft)
            .where(
                ProductTruthDraft.organization_id == organization_id,
                ProductTruthDraft.product_id == product_id,
            )
            .order_by(ProductTruthDraft.created_at.desc())
        )
    )


@router.post(
    "/product-truth-drafts/{draft_id}/request-review",
    response_model=ProductTruthDraftRead,
)
def request_truth_review(
    draft_id: UUID,
    payload: TruthReviewRequest,
    request: Request,
    session: SessionDependency,
) -> ProductTruthDraft:
    draft = session.get(ProductTruthDraft, draft_id)
    if draft is None or draft.organization_id != payload.organization_id:
        raise BuildNotFoundError("Product Truth draft was not found.")
    if draft.approval_request_id is not None:
        return draft
    approval = ApprovalWorkflowService(session).request(
        organization_id=payload.organization_id,
        project_id=None,
        requester_id=actor_id(request),
        object_type="product_truth_draft",
        object_id=draft.id,
        requested_action="product_truth.publish",
        reason=payload.reason,
    )
    draft.approval_request_id = approval.id
    draft.status = "review"
    session.add(
        DecisionQueueItem(
            organization_id=payload.organization_id,
            title="Product Truth publication review",
            domain="governance",
            reason=payload.reason,
            priority="high",
            required_action="approve",
            status="pending",
            approval_request_id=approval.id,
        )
    )
    session.commit()
    session.refresh(draft)
    return draft


@router.post(
    "/product-truth-drafts/{draft_id}/publish",
    response_model=ProductTruthDraftRead,
)
def publish_truth_draft(
    draft_id: UUID,
    payload: TruthPublishRequest,
    request: Request,
    session: SessionDependency,
) -> ProductTruthDraft:
    draft = session.get(ProductTruthDraft, draft_id)
    if draft is None or draft.organization_id != payload.organization_id:
        raise BuildNotFoundError("Product Truth draft was not found.")
    if draft.truth_id is not None:
        return draft
    approval = session.get(ApprovalRequest, payload.approval_request_id)
    if (
        approval is None
        or approval.id != draft.approval_request_id
        or approval.organization_id != payload.organization_id
        or approval.status != ApprovalStatus.APPROVED
        or approval.object_type != "product_truth_draft"
        or approval.object_id != draft.id
        or approval.requested_action != "product_truth.publish"
    ):
        raise ApiError(409, "truth_approval_required", "Approved Truth review is required.")
    actor = actor_id(request)
    user = session.get(User, actor)
    if user is None or user.principal_type != PrincipalType.HUMAN:
        raise ApiError(403, "human_authority_required", "A human actor must publish Product Truth.")
    _, truth = ProductTruthService(session).finalize(
        ProductTruthCreate(
            organization_id=payload.organization_id,
            product_id=draft.product_id,
            approval_id=approval.id,
            summary=draft.summary,
            features=draft.features,
            specifications=draft.specifications,
            approved_claims=draft.approved_claims,
            restricted_claims=draft.restricted_claims,
            usage_notes=draft.usage_notes,
        ),
        created_by=actor,
    )
    session.flush()
    draft.truth_id = truth.id
    draft.status = "approved"
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor,
        action="product_truth.created",
        entity_type="product_truth",
        entity_id=truth.id,
        metadata={
            "product_id": str(draft.product_id),
            "draft_id": str(draft.id),
            "truth_version": truth.version,
            "approval_id": str(approval.id),
            "change_reason": draft.change_reason,
        },
    )
    session.commit()
    session.refresh(draft)
    return draft


@router.get("/products/{product_id}/truth-comparison", response_model=TruthComparison)
def truth_comparison(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> TruthComparison:
    origin = product_origin(product_id, organization_id, session)
    truth = session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.organization_id == organization_id,
            ProductTruth.product_id == product_id,
        )
        .order_by(ProductTruth.version.desc())
    )
    fields: dict[str, dict[str, object | None]] = {
        "product_name": {
            "hypothesis": origin.hypothesis.name,
            "truth": origin.product.name if truth else None,
        },
        "solution_summary": {
            "hypothesis": origin.hypothesis.solution_description,
            "truth": truth.summary if truth else None,
        },
    }
    return TruthComparison(
        hypothesis_id=origin.hypothesis.id,
        product_id=product_id,
        truth=truth,
        comparable_fields=fields,
        non_comparable_fields=[
            "target_customer",
            "target_market",
            "economics_assumptions",
            "supplier_assumptions",
            "product_risks",
        ],
    )
