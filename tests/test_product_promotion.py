from uuid import UUID

from commerce_os.build.models import Product, ProductTruth
from commerce_os.build.promotion_models import ProductPromotion, ProductTruthDraft
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    Organization,
    Permission,
    Role,
)
from commerce_os.governance.rbac import RbacService
from commerce_os.intelligence.opportunity_models import MarketOpportunity, OpportunityEvidence
from commerce_os.intelligence.product_models import ProductHypothesis
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Promotion {slug}", slug=f"promotion-{slug}")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Build Brand", slug=f"brand-{slug}")
    session.add(brand)
    session.commit()
    auth = AuthenticationService(session)
    requester = auth.create_user(
        organization_id=organization.id,
        email=f"requester-{slug}@example.com",
        display_name="Requester",
        password="correct horse battery staple",
    )
    approver = auth.create_user(
        organization_id=organization.id,
        email=f"approver-{slug}@example.com",
        display_name="Approver",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=organization.id,
        name=f"approver-{slug}",
        grants_human_approval_authority=True,
    )
    permission = session.scalar(select(Permission).where(Permission.key == "approval.decide"))
    if permission is None:
        permission = Permission(
            key="approval.decide",
            resource="approval",
            action="decide",
            is_human_approval_permission=True,
        )
    session.add_all([role, permission])
    session.commit()
    rbac = RbacService(session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=requester.id)
    rbac.assign_role(
        user_id=approver.id,
        role_id=role.id,
        organization_id=organization.id,
        project_id=None,
        assigned_by=requester.id,
    )
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Cooling demand",
        description="Observed customer need.",
        category="pet",
        market="consumer",
        geography="US",
        trigger_type="customer_pain",
        timing_window="summer",
        status="qualified",
        confidence_score=0.8,
    )
    session.add(opportunity)
    session.flush()
    hypothesis = ProductHypothesis(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        name="Portable cooling mat",
        description="A product thesis.",
        customer_problem="Pets overheat while traveling.",
        solution_description="A passive portable cooling surface.",
        target_customer="Traveling pet owners",
        target_market="US pet accessories",
        status="validated",
        confidence_score=0.78,
    )
    evidence = OpportunityEvidence(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        source_type="customer_signal",
        source_reference="signal:heat",
        evidence_summary="Owners describe travel heat discomfort.",
        confidence_score=0.84,
    )
    investment = ApprovalRequest(
        organization_id=organization.id,
        project_id=None,
        requester_id=requester.id,
        object_type="market_opportunity",
        object_id=opportunity.id,
        requested_action="approve_investment",
        reason="Pursue the opportunity.",
        status=ApprovalStatus.APPROVED,
        approver_id=approver.id,
        decision_reason="Evidence supports further product definition.",
    )
    session.add_all([hypothesis, evidence, investment])
    session.commit()
    return organization, brand, requester, approver, opportunity, hypothesis


def add_economics(client: TestClient, organization_id: UUID, hypothesis_id: UUID) -> None:
    base = {"organization_id": str(organization_id)}
    economics = client.post(
        "/api/v1/product-economics",
        json=base
        | {
            "product_id": str(hypothesis_id),
            "selling_price": "40",
            "estimated_product_cost": "12",
            "estimated_shipping_cost": "5",
            "payment_cost": "1",
            "estimated_marketing_cost": "8",
            "currency": "USD",
        },
    ).json()
    for metric, value in {
        "selling_price": "40",
        "estimated_product_cost": "12",
        "estimated_shipping_cost": "5",
        "payment_cost": "1",
        "estimated_marketing_cost": "8",
    }.items():
        response = client.post(
            "/api/v1/product-economic-inputs",
            json=base
            | {
                "product_economics_id": economics["id"],
                "metric": metric,
                "value": value,
                "classification": "legacy_unprovenanced" if metric == "payment_cost" else "quoted",
                "source": (
                    "legacy_product_economics" if metric == "payment_cost" else "test evidence"
                ),
            },
        )
        assert response.status_code == 201


def test_governed_promotion_truth_versioning_and_traceability(
    client: TestClient, db_session: Session
) -> None:
    organization, brand, requester, approver, opportunity, hypothesis = foundation(
        db_session, "flow"
    )
    base = {"organization_id": str(organization.id)}
    headers = {"X-Actor-ID": str(requester.id)}
    blocked = client.get(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promotion-readiness", params=base
    )
    assert blocked.status_code == 200
    assert any(item["code"] == "critical_economics" for item in blocked.json()["items"])
    add_economics(client, organization.id, hypothesis.id)
    readiness = client.get(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promotion-readiness", params=base
    ).json()
    assert readiness["ready"] is True
    assert any(item["code"] == "legacy_economics_provenance" for item in readiness["items"])
    request = client.post(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promotion-request",
        headers=headers,
        json=base | {"brand_id": str(brand.id), "reason": "Create a governed Build product."},
    )
    assert request.status_code == 201
    promotion = request.json()
    assert promotion["product_id"] is None
    assert (
        client.post(
            f"/api/v1/product-hypotheses/{hypothesis.id}/promotion-request",
            headers=headers,
            json=base | {"brand_id": str(brand.id), "reason": "Duplicate click."},
        ).json()["id"]
        == promotion["id"]
    )
    before = db_session.scalar(select(func.count()).select_from(Product))
    pending = client.post(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promote",
        headers=headers,
        json=base | {"approval_request_id": promotion["approval_request_id"]},
    )
    assert pending.status_code == 409
    decision = client.post(
        f"/api/v1/approvals/{promotion['approval_request_id']}/decision",
        headers={"X-Actor-ID": str(approver.id)},
        json={"decision": "approved", "reason": "Promotion scope reviewed."},
    )
    assert decision.status_code == 200
    executed = client.post(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promote",
        headers=headers,
        json=base | {"approval_request_id": promotion["approval_request_id"]},
    )
    assert executed.status_code == 200
    product_id = executed.json()["product_id"]
    duplicate = client.post(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promote",
        headers=headers,
        json=base | {"approval_request_id": promotion["approval_request_id"]},
    )
    assert duplicate.json()["product_id"] == product_id
    assert db_session.scalar(select(func.count()).select_from(Product)) == before + 1
    origin = client.get(f"/api/v1/products/{product_id}/origin", params=base)
    assert origin.status_code == 200
    assert origin.json()["hypothesis"]["id"] == str(hypothesis.id)
    assert origin.json()["hypothesis"]["opportunity_id"] == str(opportunity.id)

    draft = client.post(
        f"/api/v1/products/{product_id}/product-truth-drafts",
        headers=headers,
        json=base
        | {
            "summary": "Portable cooling surface for supervised pet travel.",
            "features": ["Reusable"],
            "specifications": {"material": "provisional"},
            "approved_claims": ["Reusable"],
            "restricted_claims": ["Prevents heat illness"],
            "usage_notes": "Use under supervision.",
            "change_reason": "Initial promoted product definition.",
            "supporting_evidence": ["signal:heat"],
        },
    )
    assert draft.status_code == 201 and draft.json()["status"] == "draft"
    review = client.post(
        f"/api/v1/product-truth-drafts/{draft.json()['id']}/request-review",
        headers=headers,
        json=base | {"reason": "Review initial Product Truth."},
    )
    approval_id = review.json()["approval_request_id"]
    client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        headers={"X-Actor-ID": str(approver.id)},
        json={"decision": "approved", "reason": "Claims and evidence reviewed."},
    )
    published = client.post(
        f"/api/v1/product-truth-drafts/{draft.json()['id']}/publish",
        headers=headers,
        json=base | {"approval_request_id": approval_id},
    )
    assert published.status_code == 200 and published.json()["status"] == "approved"
    truth = db_session.get(ProductTruth, UUID(published.json()["truth_id"]))
    assert truth is not None and truth.version == 1
    comparison = client.get(f"/api/v1/products/{product_id}/truth-comparison", params=base)
    assert comparison.status_code == 200
    assert comparison.json()["truth"]["version"] == 1
    assert comparison.json()["comparable_fields"]["solution_summary"]["hypothesis"]


def test_promotion_tenant_isolation(client: TestClient, db_session: Session) -> None:
    owner, _, _, _, _, hypothesis = foundation(db_session, "owner")
    other, _, requester, _, _, _ = foundation(db_session, "other")
    response = client.post(
        f"/api/v1/product-hypotheses/{hypothesis.id}/promotion-request",
        headers={"X-Actor-ID": str(requester.id)},
        json={
            "organization_id": str(other.id),
            "brand_id": "00000000-0000-4000-8000-000000000001",
            "reason": "Cross tenant attempt.",
        },
    )
    assert response.status_code == 404
    assert owner.id != other.id


def test_truth_draft_is_append_only_until_explicit_publication(
    client: TestClient, db_session: Session
) -> None:
    organization, brand, requester, _, _, _ = foundation(db_session, "draft")
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Draft product",
        description="Draft description",
        category="pet",
        status="draft",
    )
    db_session.add(product)
    db_session.commit()
    response = client.post(
        f"/api/v1/products/{product.id}/product-truth-drafts",
        headers={"X-Actor-ID": str(requester.id)},
        json={
            "organization_id": str(organization.id),
            "summary": "Draft facts",
            "features": [],
            "specifications": {},
            "approved_claims": [],
            "restricted_claims": [],
            "usage_notes": "Draft only",
            "change_reason": "Initial draft",
            "supporting_evidence": [],
        },
    )
    assert response.status_code == 201
    assert db_session.scalar(select(func.count()).select_from(ProductTruthDraft)) == 1
    assert db_session.scalar(select(func.count()).select_from(ProductTruth)) == 0
    assert db_session.scalar(select(func.count()).select_from(ProductPromotion)) == 0
