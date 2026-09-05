from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from commerce_os.build.listing_governance_models import (
    ListingClaim,
    ListingClaimEvidence,
    ListingFAQ,
    ListingVersion,
    ListingVersionStatus,
)
from commerce_os.build.listing_governance_schemas import (
    ApproveListing,
    ClaimCreate,
    ClaimEvidenceCreate,
    ClaimEvidenceRead,
    ClaimRead,
    ClaimReviewDecision,
    FAQCreate,
    FAQRead,
    ListingPackageRead,
    ListingVersionCreate,
    ListingVersionRead,
    ReviewRequest,
    ShopifyReadinessProjection,
)
from commerce_os.build.models import Product, ProductTruth
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus, PrincipalType, User
from commerce_os.operations.models import Brand
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.listing_readiness import compose_listing_package

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


def _actor(request: Request, session: Session, organization_id: UUID) -> User:
    actor = getattr(request.state, "actor", None)
    actor_id = None if actor is None else UUID(str(actor.id))
    if actor_id is None and getattr(request.app.state, "auth_test_bypass", False):
        raw = request.headers.get("X-Actor-ID")
        actor_id = None if raw is None else UUID(raw)
    user = None if actor_id is None else session.get(User, actor_id)
    if user is None:
        raise ApiError(401, "actor_required", "Authenticated actor context is required.")
    if user.organization_id != organization_id:
        raise ApiError(403, "organization_scope", "Actor is outside this organization.")
    return user


def _human(request: Request, session: Session, organization_id: UUID) -> User:
    user = _actor(request, session, organization_id)
    if user.principal_type != PrincipalType.HUMAN:
        raise ApiError(403, "human_authority_required", "Human authority is required.")
    return user


def _listing(session: Session, listing_id: UUID, organization_id: UUID) -> ListingVersion:
    item = session.get(ListingVersion, listing_id)
    if item is None or item.organization_id != organization_id:
        raise ApiError(404, "not_found", "Listing version was not found in this organization.")
    return item


@router.post(
    "/products/{product_id}/listing-versions", response_model=ListingVersionRead, status_code=201
)
def create_listing(
    product_id: UUID, payload: ListingVersionCreate, request: Request, session: SessionDependency
) -> ListingVersion:
    actor = _human(request, session, payload.organization_id)
    product = session.get(Product, product_id)
    if product is None or product.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Product was not found in this organization.")
    truth = session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.organization_id == payload.organization_id,
            ProductTruth.product_id == product_id,
        )
        .order_by(ProductTruth.version.desc())
    )
    if truth is None:
        raise ApiError(409, "product_truth_required", "Approved Product Truth is required.")
    version = (
        session.scalar(
            select(func.max(ListingVersion.listing_version)).where(
                ListingVersion.product_id == product_id
            )
        )
        or 0
    ) + 1
    item = ListingVersion(
        **payload.model_dump(),
        product_id=product_id,
        product_truth_id=truth.id,
        product_truth_version=truth.version,
        listing_version=version,
        status="draft",
        created_by=actor.id,
    )
    session.add(item)
    session.flush()
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="listing.draft_created",
        entity_type="listing_version",
        entity_id=item.id,
        metadata={"product_id": str(product_id), "product_truth_id": str(truth.id)},
    )
    session.commit()
    session.refresh(item)
    return item


@router.get("/products/{product_id}/listing-versions", response_model=list[ListingVersionRead])
def listing_versions(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> list[ListingVersion]:
    return list(
        session.scalars(
            select(ListingVersion)
            .where(
                ListingVersion.organization_id == organization_id,
                ListingVersion.product_id == product_id,
            )
            .order_by(ListingVersion.listing_version.desc())
        )
    )


@router.post("/listing-versions/{listing_id}/claims", response_model=ClaimRead, status_code=201)
def create_claim(
    listing_id: UUID, payload: ClaimCreate, request: Request, session: SessionDependency
) -> ListingClaim:
    actor = _human(request, session, payload.organization_id)
    listing = _listing(session, listing_id, payload.organization_id)
    if listing.status in {"approved", "superseded"}:
        raise ApiError(409, "immutable_listing", "Approved Listing versions are immutable.")
    item = ListingClaim(
        **payload.model_dump(),
        listing_version_id=listing.id,
        product_id=listing.product_id,
        support_status="unknown",
        risk_category="high"
        if payload.claim_type
        in {"performance", "compliance", "comparative", "sustainability", "health_or_safety"}
        else "standard",
        review_status="pending",
        human_review_required=payload.claim_type
        in {"performance", "compliance", "comparative", "sustainability", "health_or_safety"},
        blocking=True,
        created_by=actor.id,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post(
    "/listing-claims/{claim_id}/evidence", response_model=ClaimEvidenceRead, status_code=201
)
def add_claim_evidence(
    claim_id: UUID, payload: ClaimEvidenceCreate, request: Request, session: SessionDependency
) -> ListingClaimEvidence:
    _human(request, session, payload.organization_id)
    claim = session.get(ListingClaim, claim_id)
    if claim is None or claim.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Claim was not found in this organization.")
    listing = _listing(session, claim.listing_version_id, payload.organization_id)
    if listing.status in {"approved", "superseded"}:
        raise ApiError(409, "immutable_listing", "Approved Listing versions are immutable.")
    item = ListingClaimEvidence(**payload.model_dump(), claim_id=claim_id)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/listing-claims/{claim_id}/review", response_model=ClaimRead)
def review_claim(
    claim_id: UUID, payload: ClaimReviewDecision, request: Request, session: SessionDependency
) -> ListingClaim:
    actor = _human(request, session, payload.organization_id)
    claim = session.get(ListingClaim, claim_id)
    if claim is None or claim.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Claim was not found in this organization.")
    compose_listing_package(session, payload.organization_id, claim.product_id)
    if payload.decision == "approved" and claim.support_status not in {"supported", "conditional"}:
        raise ApiError(
            409,
            "claim_support_required",
            "Unsupported, prohibited, or unknown claims cannot be approved.",
        )
    claim.review_status = payload.decision
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action=f"listing_claim.{payload.decision}",
        entity_type="listing_claim",
        entity_id=claim.id,
        metadata={"reason": payload.reason},
    )
    session.commit()
    session.refresh(claim)
    return claim


@router.delete("/listing-claims/{claim_id}", status_code=204)
def remove_claim(
    claim_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> Response:
    actor = _human(request, session, organization_id)
    claim = session.get(ListingClaim, claim_id)
    if claim is None or claim.organization_id != organization_id:
        raise ApiError(404, "not_found", "Claim was not found in this organization.")
    listing = _listing(session, claim.listing_version_id, organization_id)
    if listing.status in {"approved", "superseded"}:
        raise ApiError(409, "immutable_listing", "Approved Listing versions are immutable.")
    AuditService(session).record(
        organization_id=organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="listing_claim.removed",
        entity_type="listing_claim",
        entity_id=claim.id,
        metadata={"listing_version_id": str(listing.id)},
    )
    session.delete(claim)
    session.commit()
    return Response(status_code=204)


@router.post("/listing-versions/{listing_id}/faqs", response_model=FAQRead, status_code=201)
def create_faq(
    listing_id: UUID, payload: FAQCreate, request: Request, session: SessionDependency
) -> ListingFAQ:
    _human(request, session, payload.organization_id)
    listing = _listing(session, listing_id, payload.organization_id)
    if listing.status in {"approved", "superseded"}:
        raise ApiError(409, "immutable_listing", "Approved Listing versions are immutable.")
    if payload.answer_status == "supported_answer" and (
        not payload.answer or not payload.evidence_reference
    ):
        raise ApiError(
            422,
            "faq_evidence_required",
            "Supported FAQ answers require an answer and evidence reference.",
        )
    item = ListingFAQ(**payload.model_dump(), listing_version_id=listing.id)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/products/{product_id}/listing-package", response_model=ListingPackageRead)
def listing_package(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> ListingPackageRead:
    try:
        return compose_listing_package(session, organization_id, product_id)
    except LookupError as exc:
        raise ApiError(404, "not_found", str(exc)) from exc


@router.get("/listing-packages", response_model=list[ListingPackageRead])
def listing_packages(organization_id: UUID, session: SessionDependency) -> list[ListingPackageRead]:
    ids = session.scalars(
        select(Product.id)
        .where(Product.organization_id == organization_id)
        .order_by(Product.created_at.desc())
    )
    return [compose_listing_package(session, organization_id, item) for item in ids]


@router.post("/listing-versions/{listing_id}/request-review", response_model=ListingVersionRead)
def request_review(
    listing_id: UUID, payload: ReviewRequest, request: Request, session: SessionDependency
) -> ListingVersion:
    actor = _human(request, session, payload.organization_id)
    listing = _listing(session, listing_id, payload.organization_id)
    package = compose_listing_package(session, payload.organization_id, listing.product_id)
    if package.blockers:
        raise ApiError(409, "listing_not_ready", "Listing readiness blockers remain.")
    approval = ApprovalWorkflowService(session).request(
        organization_id=payload.organization_id,
        project_id=None,
        requester_id=actor.id,
        object_type="listing_version",
        object_id=listing.id,
        requested_action="listing.approve",
        reason=payload.reason,
        commit=False,
    )
    listing.approval_request_id = approval.id
    listing.status = ListingVersionStatus.REVIEW
    session.add(
        DecisionQueueItem(
            organization_id=payload.organization_id,
            title=f"Listing approval: {listing.title}",
            domain="governance",
            reason=payload.reason,
            priority="high",
            required_action="approve",
            status="pending",
            approval_request_id=approval.id,
        )
    )
    session.commit()
    session.refresh(listing)
    return listing


@router.post("/listing-versions/{listing_id}/approve", response_model=ListingVersionRead)
def approve_listing(
    listing_id: UUID, payload: ApproveListing, request: Request, session: SessionDependency
) -> ListingVersion:
    actor = _human(request, session, payload.organization_id)
    listing = _listing(session, listing_id, payload.organization_id)
    approval = session.get(ApprovalRequest, payload.approval_request_id)
    if (
        approval is None
        or approval.id != listing.approval_request_id
        or approval.status != ApprovalStatus.APPROVED
        or approval.object_id != listing.id
        or approval.requested_action != "listing.approve"
    ):
        raise ApiError(409, "listing_approval_required", "Approved Listing review is required.")
    if compose_listing_package(session, payload.organization_id, listing.product_id).blockers:
        raise ApiError(409, "listing_not_ready", "Listing readiness blockers remain.")
    older = session.scalars(
        select(ListingVersion).where(
            ListingVersion.organization_id == payload.organization_id,
            ListingVersion.product_id == listing.product_id,
            ListingVersion.status == "approved",
            ListingVersion.id != listing.id,
        )
    )
    for item in older:
        item.status = ListingVersionStatus.SUPERSEDED
    listing.status = ListingVersionStatus.APPROVED
    listing.approved_by = actor.id
    listing.approved_at = datetime.now(UTC)
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="listing.approved",
        entity_type="listing_version",
        entity_id=listing.id,
        metadata={"publication_authorized": False},
    )
    session.commit()
    session.refresh(listing)
    return listing


@router.get("/products/{product_id}/shopify-readiness", response_model=ShopifyReadinessProjection)
def shopify_readiness(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> ShopifyReadinessProjection:
    package = compose_listing_package(session, organization_id, product_id)
    listing = package.listing
    if listing is None:
        raise ApiError(409, "listing_required", "A Listing version is required.")
    product = session.get(Product, product_id)
    brand = None if product is None else session.get(Brand, product.brand_id)
    missing = [
        name
        for name, value in {
            "price": listing.commercial_price if listing.price_status == "approved" else None,
            "currency": listing.currency,
            "structured_attributes": listing.structured_attributes,
        }.items()
        if not value
    ]
    return ShopifyReadinessProjection(
        title=listing.title,
        description=listing.description,
        product_type="" if product is None else product.category,
        vendor=None if brand is None else brand.name,
        price=listing.commercial_price if listing.price_status == "approved" else None,
        currency=listing.currency if listing.price_status == "approved" else None,
        seo_title=listing.seo_title,
        seo_description=listing.meta_description,
        metafield_candidates=listing.structured_attributes,
        missing_fields=missing,
    )
