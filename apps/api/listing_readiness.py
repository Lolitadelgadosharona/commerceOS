from uuid import UUID

from commerce_os.build.listing_governance_models import (
    ListingClaim,
    ListingClaimEvidence,
    ListingFAQ,
    ListingVersion,
)
from commerce_os.build.listing_governance_schemas import (
    AllowedFact,
    ClaimReviewItem,
    ListingPackageRead,
    ReadinessItem,
)
from commerce_os.build.models import Product, ProductClaimPolicy, ProductTruth
from commerce_os.build.promotion_models import ProductPromotion
from commerce_os.build.readiness_models import ProductBuildRequirement
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.build_readiness import compose_build_package

HIGH_RISK = {"performance", "compliance", "comparative", "sustainability", "health_or_safety"}
STRONG_EVIDENCE = {"product_truth", "build_requirement", "supplier_evidence", "approved_policy"}


def _current_truth(
    session: Session, organization_id: UUID, product_id: UUID
) -> ProductTruth | None:
    return session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.organization_id == organization_id, ProductTruth.product_id == product_id
        )
        .order_by(ProductTruth.version.desc())
    )


def compose_listing_package(
    session: Session, organization_id: UUID, product_id: UUID
) -> ListingPackageRead:
    product = session.get(Product, product_id)
    if product is None or product.organization_id != organization_id:
        raise LookupError("Product was not found in this organization.")
    truth = _current_truth(session, organization_id, product_id)
    listing = session.scalar(
        select(ListingVersion)
        .where(
            ListingVersion.organization_id == organization_id,
            ListingVersion.product_id == product_id,
            ListingVersion.status != "superseded",
        )
        .order_by(ListingVersion.listing_version.desc())
    )
    claims = (
        []
        if listing is None
        else list(
            session.scalars(
                select(ListingClaim).where(
                    ListingClaim.organization_id == organization_id,
                    ListingClaim.listing_version_id == listing.id,
                )
            )
        )
    )
    faqs = (
        []
        if listing is None
        else list(
            session.scalars(
                select(ListingFAQ).where(
                    ListingFAQ.organization_id == organization_id,
                    ListingFAQ.listing_version_id == listing.id,
                )
            )
        )
    )
    policies = {
        p.claim_type: p
        for p in session.scalars(
            select(ProductClaimPolicy).where(
                ProductClaimPolicy.organization_id == organization_id,
                ProductClaimPolicy.brand_id == product.brand_id,
            )
        )
    }
    build = compose_build_package(session, organization_id, product_id)

    allowed: list[AllowedFact] = []
    if truth:
        allowed.extend(
            AllowedFact(
                fact=f,
                source=f"ProductTruth v{truth.version}",
                evidence=[str(truth.id)],
                can_use=True,
                restrictions=[],
                notes="Approved Product Truth feature.",
            )
            for f in truth.features
        )
        allowed.extend(
            AllowedFact(
                fact=f"{k}: {v}",
                source=f"ProductTruth v{truth.version}",
                evidence=[str(truth.id)],
                can_use=True,
                restrictions=[],
                notes="Approved structured specification.",
            )
            for k, v in truth.specifications.items()
        )
        allowed.extend(
            AllowedFact(
                fact=c,
                source=f"ProductTruth v{truth.version}",
                evidence=[str(truth.id)],
                can_use=True,
                restrictions=[],
                notes="Explicitly approved claim.",
            )
            for c in truth.approved_claims
        )
        allowed.extend(
            AllowedFact(
                fact=c,
                source=f"ProductTruth v{truth.version}",
                evidence=[str(truth.id)],
                can_use=False,
                restrictions=["restricted_claim"],
                notes="Must not be used without a new governed truth decision.",
            )
            for c in truth.restricted_claims
        )

    review: list[ClaimReviewItem] = []
    for claim in claims:
        evidence = list(
            session.scalars(
                select(ListingClaimEvidence).where(
                    ListingClaimEvidence.organization_id == organization_id,
                    ListingClaimEvidence.claim_id == claim.id,
                )
            )
        )
        policy = policies.get(claim.claim_type)
        restricted = bool(
            truth and claim.claim_text.casefold() in {x.casefold() for x in truth.restricted_claims}
        )
        high = claim.claim_type in HIGH_RISK
        strong = any(
            e.source_type in STRONG_EVIDENCE and e.classification in {"verified", "approved"}
            for e in evidence
        )
        any_support = any(
            e.classification in {"verified", "approved", "observed"} for e in evidence
        )
        if restricted or (policy and not policy.allowed):
            support = "prohibited"
        elif high and not policy:
            support = "unknown"
        elif (high or (policy and policy.evidence_required)) and strong:
            support = "conditional"
        elif any_support:
            support = "supported"
        else:
            support = "unknown" if not evidence else "unsupported"
        blocking = support in {"unknown", "unsupported", "prohibited"} or (
            high and support != "supported" and claim.review_status != "approved"
        )
        claim.support_status = support
        claim.risk_category = "high" if high else "standard"
        claim.human_review_required = high
        claim.blocking = blocking
        review.append(
            ClaimReviewItem(
                id=claim.id,
                claim=claim.claim_text,
                claim_type=claim.claim_type,
                support_status=support,
                sources=[f"{e.source_type}:{e.source_reference}" for e in evidence],
                risk_level=claim.risk_category,
                policy_requirement="Explicit policy and strong evidence required."
                if high
                else None,
                human_review_needed=high,
                blocking=blocking,
            )
        )

    blockers: list[ReadinessItem] = []
    warnings: list[ReadinessItem] = []
    promotion = session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == organization_id,
            ProductPromotion.product_id == product_id,
        )
    )
    if promotion is None:
        blockers.append(
            ReadinessItem(
                code="governed_product",
                severity="blocker",
                message="Governed Product origin is required.",
            )
        )
    if truth is None:
        blockers.append(
            ReadinessItem(
                code="product_truth",
                severity="blocker",
                message="Approved Product Truth is required.",
            )
        )
    if listing is None:
        blockers.append(
            ReadinessItem(
                code="listing_draft", severity="blocker", message="Create a Listing draft."
            )
        )
    elif truth and listing.product_truth_id != truth.id:
        blockers.append(
            ReadinessItem(
                code="stale_product_truth",
                severity="blocker",
                message="PRODUCT TRUTH CHANGED — LISTING REVIEW REQUIRED.",
                references=[str(truth.id)],
            )
        )
    if build.blockers:
        blockers.append(
            ReadinessItem(
                code="build_ready",
                severity="blocker",
                message="Build blockers must be resolved before Listing approval.",
            )
        )
    blockers.extend(
        ReadinessItem(
            code=f"claim_{r.support_status}",
            severity="blocker",
            message=f"Claim is {r.support_status}: {r.claim}",
            references=[str(r.id)],
        )
        for r in review
        if r.blocking
    )
    if listing and listing.price_status != "approved":
        blockers.append(
            ReadinessItem(
                code="commercial_price",
                severity="blocker",
                message="Commercial Listing price requires explicit approval.",
            )
        )
    required_listing = (
        []
        if truth is None
        else list(
            session.scalars(
                select(ProductBuildRequirement).where(
                    ProductBuildRequirement.organization_id == organization_id,
                    ProductBuildRequirement.product_truth_id == truth.id,
                    ProductBuildRequirement.required_for_listing.is_(True),
                )
            )
        )
    )
    if listing:
        missing = [
            r.display_label
            for r in required_listing
            if r.attribute_key not in listing.structured_attributes
            and r.attribute_key not in listing.specifications
        ]
        if missing:
            blockers.append(
                ReadinessItem(
                    code="structured_attributes",
                    severity="blocker",
                    message="Required Listing attributes are missing.",
                    references=missing,
                )
            )
        if not listing.warnings and any(r.risk_level == "high" for r in review):
            blockers.append(
                ReadinessItem(
                    code="required_warnings",
                    severity="blocker",
                    message="High-risk content requires explicit warnings.",
                )
            )
        if not faqs or any(f.answer_status != "supported_answer" for f in faqs):
            warnings.append(
                ReadinessItem(
                    code="faq_incomplete",
                    severity="warning",
                    message="FAQ contains incomplete or unreviewed answers.",
                )
            )
        if not listing.seo_title or not listing.meta_description:
            warnings.append(
                ReadinessItem(
                    code="seo_incomplete", severity="warning", message="SEO metadata is incomplete."
                )
            )
        if not listing.customer_problem:
            warnings.append(
                ReadinessItem(
                    code="customer_language_limited",
                    severity="warning",
                    message="Customer-language evidence is limited.",
                )
            )
        if len(review) < 2:
            warnings.append(
                ReadinessItem(
                    code="optional_proof_weak",
                    severity="warning",
                    message="Optional proof coverage is limited.",
                )
            )
    status = "not_ready" if blockers else "conditional" if warnings else "ready"
    next_action = (
        "Create a governed Listing draft."
        if listing is None
        else (
            blockers[0].message
            if blockers
            else "Request human Listing approval."
            if listing.status == "draft"
            else "Approved Listing Truth is ready for a future channel projection."
        )
    )
    return ListingPackageRead(
        organization_id=organization_id,
        product_id=product_id,
        product_name=product.name,
        product_truth_id=None if truth is None else truth.id,
        product_truth_version=None if truth is None else truth.version,
        listing=listing,
        allowed_facts=allowed,
        claim_review=review,
        faqs=faqs,
        blockers=blockers,
        warnings=warnings,
        status=status,
        product_truth_fresh=bool(listing and truth and listing.product_truth_id == truth.id),
        build_status=build.status,
        structured_data_ready=bool(
            listing and listing.title and listing.description and listing.structured_attributes
        ),
        next_action=next_action,
        origin_opportunity_id=build.origin_opportunity_id,
        origin_hypothesis_id=build.origin_hypothesis_id,
    )
