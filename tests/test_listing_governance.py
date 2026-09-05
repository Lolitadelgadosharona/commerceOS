from datetime import date, timedelta
from uuid import UUID

from commerce_os.build.listing_governance_models import (
    ListingClaim,
    ListingClaimEvidence,
    ListingFAQ,
    ListingVersion,
)
from commerce_os.build.models import ProductClaimPolicy, ProductTruth
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalStatus, Permission, Role
from commerce_os.governance.rbac import RbacService
from commerce_os.intelligence.supplier_models import SupplierEvidence
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.listing_readiness import compose_listing_package
from tests.test_build_readiness import build_foundation


def ready_foundation(session: Session, slug: str = "listing") -> dict[str, object]:
    state = build_foundation(session, slug)
    supplier = state["supplier"]
    quote = state["quote"]
    session.add(
        SupplierEvidence(
            organization_id=state["organization"].id,
            supplier_id=supplier.id,
            field_name="material",
            value="cotton",
            classification="verified",
            source="reviewed specification",
            confidence=0.95,
            evidence_reference="spec:material",
        )
    )
    quote.valid_until = date.today() + timedelta(days=30)
    session.commit()
    return state


def draft(session: Session, state: dict[str, object]) -> ListingVersion:
    truth = state["truth"]
    product = state["product"]
    user = state["user"]
    item = ListingVersion(
        organization_id=state["organization"].id,
        product_id=product.id,
        product_truth_id=truth.id,
        product_truth_version=truth.version,
        listing_version=1,
        status="draft",
        title="Governed Product",
        subtitle="Evidence-backed",
        summary="Approved facts only.",
        description="A factual product description.",
        customer_problem="Customers need a washable option.",
        solution="A washable cotton product.",
        features=["washable"],
        benefits=["Easier care"],
        specifications={"material": "cotton"},
        use_cases=["home"],
        whats_included=["product"],
        warnings=[],
        care_usage="Follow care instructions.",
        shipping_facts=None,
        return_facts=None,
        risk_reversal=None,
        seo_title="Governed cotton product",
        meta_description="A washable cotton product.",
        slug_suggestion="governed-cotton-product",
        primary_topic="cotton product",
        secondary_topics=[],
        structured_attributes={"material": "cotton"},
        commercial_price=40,
        currency="USD",
        price_status="approved",
        change_reason="Initial governed draft",
        created_by=user.id,
    )
    session.add(item)
    session.commit()
    return item


def test_claim_review_blocks_unknown_then_supports_with_evidence(db_session: Session) -> None:
    state = ready_foundation(db_session)
    item = draft(db_session, state)
    claim = ListingClaim(
        organization_id=state["organization"].id,
        listing_version_id=item.id,
        product_id=state["product"].id,
        claim_text="washable",
        claim_type="product_fact",
        classification="fact",
        support_status="unknown",
        risk_category="standard",
        review_status="pending",
        human_review_required=False,
        blocking=True,
        created_by=state["user"].id,
    )
    db_session.add(claim)
    db_session.commit()
    blocked = compose_listing_package(db_session, state["organization"].id, state["product"].id)
    assert blocked.status == "not_ready" and blocked.claim_review[0].support_status == "unknown"
    db_session.add(
        ListingClaimEvidence(
            organization_id=state["organization"].id,
            claim_id=claim.id,
            source_type="product_truth",
            source_reference=str(state["truth"].id),
            evidence_text="Approved claim",
            classification="approved",
        )
    )
    db_session.commit()
    ready = compose_listing_package(db_session, state["organization"].id, state["product"].id)
    assert ready.status == "conditional" and ready.claim_review[0].support_status == "supported"


def test_high_risk_policy_and_human_review_are_required(db_session: Session) -> None:
    state = ready_foundation(db_session, "risk")
    item = draft(db_session, state)
    claim = ListingClaim(
        organization_id=state["organization"].id,
        listing_version_id=item.id,
        product_id=state["product"].id,
        claim_text="Clinically proven",
        claim_type="health_or_safety",
        classification="fact",
        support_status="unknown",
        risk_category="high",
        review_status="pending",
        human_review_required=True,
        blocking=True,
        created_by=state["user"].id,
    )
    db_session.add(claim)
    db_session.commit()
    assert (
        compose_listing_package(db_session, state["organization"].id, state["product"].id)
        .claim_review[0]
        .support_status
        == "unknown"
    )
    db_session.add(
        ProductClaimPolicy(
            organization_id=state["organization"].id,
            brand_id=state["product"].brand_id,
            claim_type="health_or_safety",
            allowed=True,
            reason="Strong evidence and human review required",
            evidence_required=True,
        )
    )
    db_session.add(
        ListingClaimEvidence(
            organization_id=state["organization"].id,
            claim_id=claim.id,
            source_type="approved_policy",
            source_reference="policy:health",
            evidence_text="Reviewed policy evidence",
            classification="approved",
        )
    )
    claim.review_status = "approved"
    item.warnings = ["Follow usage guidance."]
    db_session.commit()
    result = compose_listing_package(db_session, state["organization"].id, state["product"].id)
    assert (
        result.claim_review[0].support_status == "conditional"
        and not result.claim_review[0].blocking
    )


def test_product_truth_change_marks_listing_stale(db_session: Session) -> None:
    state = ready_foundation(db_session, "stale")
    draft(db_session, state)
    original = state["truth"]
    db_session.add(
        ProductTruth(
            organization_id=state["organization"].id,
            product_id=state["product"].id,
            version=2,
            summary="Updated",
            features=original.features,
            specifications=original.specifications,
            approved_claims=original.approved_claims,
            restricted_claims=original.restricted_claims,
            usage_notes=original.usage_notes,
            created_by=state["user"].id,
            approval_id=state["truth"].approval_id,
        )
    )
    # ProductTruth approval is unique, so use a fresh approval through the fixture shortcut.
    db_session.rollback()
    from commerce_os.governance.models import ApprovalRequest, ApprovalStatus

    approval = ApprovalRequest(
        organization_id=state["organization"].id,
        requester_id=state["user"].id,
        object_type="product_truth_draft",
        object_id=state["product"].id,
        requested_action="product_truth.publish",
        reason="Updated truth",
        status=ApprovalStatus.APPROVED,
        approver_id=state["user"].id,
    )
    db_session.add(approval)
    db_session.flush()
    db_session.add(
        ProductTruth(
            organization_id=state["organization"].id,
            product_id=state["product"].id,
            version=2,
            summary="Updated",
            features=original.features,
            specifications=original.specifications,
            approved_claims=original.approved_claims,
            restricted_claims=original.restricted_claims,
            usage_notes=original.usage_notes,
            created_by=state["user"].id,
            approval_id=approval.id,
        )
    )
    db_session.commit()
    result = compose_listing_package(db_session, state["organization"].id, state["product"].id)
    assert not result.product_truth_fresh and any(
        x.code == "stale_product_truth" for x in result.blockers
    )


def test_faq_supported_answer_requires_evidence_and_warning_does_not_block(
    db_session: Session,
) -> None:
    state = ready_foundation(db_session, "faq")
    item = draft(db_session, state)
    db_session.add(
        ListingFAQ(
            organization_id=state["organization"].id,
            listing_version_id=item.id,
            question="How do I care for it?",
            answer="Follow care instructions.",
            answer_status="supported_answer",
            evidence_reference=str(state["truth"].id),
        )
    )
    db_session.commit()
    result = compose_listing_package(db_session, state["organization"].id, state["product"].id)
    assert result.status == "conditional" and not result.blockers and result.warnings


def test_api_cross_tenant_denial_and_shopify_is_read_only(
    client: TestClient, db_session: Session
) -> None:
    state = ready_foundation(db_session, "api")
    item = draft(db_session, state)
    headers = {"X-Actor-ID": str(state["user"].id)}
    package = client.get(
        f"/api/v1/products/{state['product'].id}/listing-package",
        params={"organization_id": str(state["organization"].id)},
        headers=headers,
    )
    assert package.status_code == 200
    shopify = client.get(
        f"/api/v1/products/{state['product'].id}/shopify-readiness",
        params={"organization_id": str(state["organization"].id)},
        headers=headers,
    )
    assert shopify.status_code == 200
    assert (
        shopify.json()["external_id"] is None and shopify.json()["publication_authorized"] is False
    )
    other = ready_foundation(db_session, "other")
    denied = client.post(
        f"/api/v1/listing-versions/{item.id}/claims",
        headers={"X-Actor-ID": str(other["user"].id)},
        json={
            "organization_id": str(state["organization"].id),
            "claim_text": "washable",
            "claim_type": "feature",
            "classification": "fact",
        },
    )
    assert denied.status_code == 403


def test_remove_unsupported_claim_then_request_listing_review(
    client: TestClient, db_session: Session
) -> None:
    state = ready_foundation(db_session, "review")
    item = draft(db_session, state)
    claim = ListingClaim(
        organization_id=state["organization"].id,
        listing_version_id=item.id,
        product_id=state["product"].id,
        claim_text="Guaranteed result",
        claim_type="performance",
        classification="assumption",
        support_status="unknown",
        risk_category="high",
        review_status="pending",
        human_review_required=True,
        blocking=True,
        created_by=state["user"].id,
    )
    db_session.add(claim)
    db_session.commit()
    headers = {"X-Actor-ID": str(state["user"].id)}
    removed = client.delete(
        f"/api/v1/listing-claims/{claim.id}",
        params={"organization_id": str(state["organization"].id)},
        headers=headers,
    )
    assert removed.status_code == 204
    review = client.post(
        f"/api/v1/listing-versions/{item.id}/request-review",
        headers=headers,
        json={
            "organization_id": str(state["organization"].id),
            "reason": "All deterministic Listing blockers are resolved.",
        },
    )
    assert review.status_code == 200
    assert review.json()["status"] == "review"
    assert review.json()["approval_request_id"] is not None


def test_human_listing_approval_is_immutable_and_does_not_publish(
    client: TestClient, db_session: Session
) -> None:
    state = ready_foundation(db_session, "approval")
    item = draft(db_session, state)
    organization = state["organization"]
    requester = state["user"]
    approver = AuthenticationService(db_session).create_user(
        organization_id=organization.id,
        email="listing-approver@example.com",
        display_name="Listing Approver",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=organization.id,
        name="listing-approver",
        grants_human_approval_authority=True,
    )
    permission = Permission(
        key="approval.decide",
        resource="approval",
        action="decide",
        is_human_approval_permission=True,
    )
    db_session.add_all([role, permission])
    db_session.commit()
    rbac = RbacService(db_session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=requester.id)
    rbac.assign_role(
        user_id=approver.id,
        role_id=role.id,
        organization_id=organization.id,
        project_id=None,
        assigned_by=requester.id,
    )
    requested = client.post(
        f"/api/v1/listing-versions/{item.id}/request-review",
        headers={"X-Actor-ID": str(requester.id)},
        json={
            "organization_id": str(organization.id),
            "reason": "Governed Listing package is ready for human review.",
        },
    )
    assert requested.status_code == 200
    approval_id = UUID(requested.json()["approval_request_id"])
    ApprovalWorkflowService(db_session).decide(
        approval_id=approval_id,
        approver_id=approver.id,
        decision=ApprovalStatus.APPROVED,
        reason="Claims and commercial content verified.",
    )
    approved = client.post(
        f"/api/v1/listing-versions/{item.id}/approve",
        headers={"X-Actor-ID": str(approver.id)},
        json={
            "organization_id": str(organization.id),
            "approval_request_id": str(approval_id),
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    projection = client.get(
        f"/api/v1/products/{state['product'].id}/shopify-readiness",
        params={"organization_id": str(organization.id)},
        headers={"X-Actor-ID": str(approver.id)},
    )
    assert projection.status_code == 200
    assert projection.json()["publication_authorized"] is False
    assert projection.json()["external_id"] is None
    immutable = client.post(
        f"/api/v1/listing-versions/{item.id}/claims",
        headers={"X-Actor-ID": str(approver.id)},
        json={
            "organization_id": str(organization.id),
            "claim_text": "A late claim",
            "claim_type": "feature",
            "classification": "fact",
        },
    )
    assert immutable.status_code == 409
