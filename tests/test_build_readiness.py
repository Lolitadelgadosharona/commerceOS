from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from commerce_os.build.models import Product, ProductTruth
from commerce_os.build.promotion_models import ProductPromotion
from commerce_os.build.readiness_models import (
    BuildRequirementPolicy,
    ProductSample,
    SupplierCandidatePromotion,
)
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus, Organization
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.intelligence.product_models import (
    ProductEconomicInputProvenance,
    ProductEconomics,
    ProductHypothesis,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.intelligence.supplier_models import (
    ApprovedProductSupplier,
    SupplierEvidence,
    SupplierProfile,
    SupplierQuote,
    SupplierRisk,
)
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.build_readiness import compose_build_package


def build_foundation(session: Session, slug: str = "build") -> dict[str, object]:
    organization = Organization(name=f"Build {slug}", slug=f"build-{slug}")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Build Brand", slug=f"brand-{slug}")
    session.add(brand)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"builder-{slug}@example.com",
        display_name="Builder",
        password="correct horse battery staple",
    )
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Evidence-backed opportunity",
        description="Customer problem evidence.",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="demand",
        timing_window="current",
        status="qualified",
        confidence_score=0.8,
    )
    session.add(opportunity)
    session.flush()
    hypothesis = ProductHypothesis(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        name="Governed product",
        description="Hypothesis",
        customer_problem="Observed pain",
        solution_description="Defined solution",
        target_customer="Target customer",
        target_market="US",
        status="validated",
        confidence_score=0.8,
    )
    session.add(hypothesis)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Governed product",
        description="Canonical Product",
        category="home",
        status="approved",
    )
    supplier = SupplierProfile(
        organization_id=organization.id,
        name="Build Supplier",
        source_type="manufacturer",
        country="Portugal",
        capabilities=["textiles"],
        certifications=[],
        status="evaluating",
    )
    session.add_all([product, supplier])
    session.flush()
    promotion_approval = ApprovalRequest(
        organization_id=organization.id,
        requester_id=user.id,
        object_type="product_hypothesis",
        object_id=hypothesis.id,
        requested_action="product.promote",
        reason="Governed promotion",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
    )
    truth_approval = ApprovalRequest(
        organization_id=organization.id,
        requester_id=user.id,
        object_type="product_truth_draft",
        object_id=product.id,
        requested_action="product_truth.publish",
        reason="Truth approval",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
    )
    supplier_approval = ApprovalRequest(
        organization_id=organization.id,
        requester_id=user.id,
        object_type="product_supplier_selection",
        object_id=supplier.id,
        requested_action="supplier.select",
        reason="Supplier approval",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
    )
    session.add_all([promotion_approval, truth_approval, supplier_approval])
    session.flush()
    promotion = ProductPromotion(
        organization_id=organization.id,
        product_hypothesis_id=hypothesis.id,
        opportunity_id=opportunity.id,
        brand_id=brand.id,
        approval_request_id=promotion_approval.id,
        product_id=product.id,
        requested_by=user.id,
        promoted_by=user.id,
        promoted_at=datetime.now(UTC),
        status="promoted",
    )
    truth = ProductTruth(
        organization_id=organization.id,
        product_id=product.id,
        version=1,
        summary="Approved truth",
        features=["washable"],
        specifications={"material": "cotton"},
        approved_claims=["washable"],
        restricted_claims=[],
        usage_notes="Follow care instructions.",
        created_by=user.id,
        approval_id=truth_approval.id,
    )
    relationship = ApprovedProductSupplier(
        organization_id=organization.id,
        product_id=product.id,
        supplier_id=supplier.id,
        approval_request_id=supplier_approval.id,
        role="primary",
        status="approved",
        approved_by=user.id,
        approved_at=datetime.now(UTC),
    )
    economics = ProductEconomics(
        organization_id=organization.id,
        product_id=hypothesis.id,
        selling_price=Decimal("40"),
        estimated_product_cost=Decimal("12"),
        estimated_shipping_cost=Decimal("5"),
        payment_cost=Decimal("1"),
        estimated_marketing_cost=Decimal("8"),
        contribution_margin=Decimal("14"),
        margin_percentage=Decimal("35"),
        currency="USD",
    )
    session.add_all([promotion, truth, relationship, economics])
    session.flush()
    quote = SupplierQuote(
        organization_id=organization.id,
        supplier_id=supplier.id,
        product_id=product.id,
        currency="USD",
        unit_price=Decimal("12"),
        minimum_order_quantity=100,
        price_tiers=[],
        sample_cost=Decimal("20"),
        tooling_cost=None,
        packaging_cost=Decimal("1"),
        incoterm="EXW",
        payment_terms="30/70",
        lead_time="30 days",
        quote_date=date.today() - timedelta(days=40),
        valid_until=date.today() - timedelta(days=10),
        classification="quoted",
        source="fixture quote",
        confidence=0.9,
        evidence_reference="quote:fixture",
        notes=None,
    )
    session.add(quote)
    session.flush()
    session.add(
        ProductEconomicInputProvenance(
            organization_id=organization.id,
            product_economics_id=economics.id,
            supplier_quote_id=quote.id,
            metric="estimated_product_cost",
            value=Decimal("12"),
            classification="quoted",
            source="fixture quote",
            confidence=0.9,
            as_of=datetime.now(UTC),
            evidence_reference="quote:fixture",
            notes="Not Finance actual",
        )
    )
    session.commit()
    return {
        "organization": organization,
        "user": user,
        "product": product,
        "truth": truth,
        "supplier": supplier,
        "relationship": relationship,
        "hypothesis": hypothesis,
        "quote": quote,
        "economics": economics,
    }


def test_build_package_resolves_evidence_blocker_but_keeps_warning(db_session: Session) -> None:
    state = build_foundation(db_session)
    organization = state["organization"]
    product = state["product"]
    supplier = state["supplier"]
    first = compose_build_package(db_session, organization.id, product.id)
    assert first.status == "not_ready"
    assert any(item.code == "supplier_fit" for item in first.blockers)
    db_session.add(
        SupplierEvidence(
            organization_id=organization.id,
            supplier_id=supplier.id,
            field_name="material",
            value="cotton",
            classification="verified",
            source="human reviewed specification",
            confidence=0.95,
            evidence_reference="spec:material",
        )
    )
    db_session.commit()
    resolved = compose_build_package(db_session, organization.id, product.id)
    assert resolved.status == "conditional"
    assert resolved.blockers == []
    assert any(item.code == "expired_quote" for item in resolved.warnings)
    assert resolved.supplier_fit[0].status == "pass"
    assert resolved.origin_opportunity_id is not None


def test_sample_unknown_never_passes_and_review_resolves_policy(db_session: Session) -> None:
    state = build_foundation(db_session, "sample")
    organization = state["organization"]
    product = state["product"]
    supplier = state["supplier"]
    user = state["user"]
    relationship = state["relationship"]
    db_session.add_all(
        [
            SupplierEvidence(
                organization_id=organization.id,
                supplier_id=supplier.id,
                field_name="material",
                value="cotton",
                classification="verified",
                source="reviewed spec",
                confidence=0.9,
            ),
            BuildRequirementPolicy(
                organization_id=organization.id,
                product_id=product.id,
                sample_required=True,
                inspection_required=False,
                compliance_evidence_required=False,
                packaging_validation_required=False,
                reason="Risk-based sample policy",
            ),
        ]
    )
    sample = ProductSample(
        organization_id=organization.id,
        product_id=product.id,
        supplier_id=supplier.id,
        approved_product_supplier_id=relationship.id,
        sample_identifier="SAMPLE-001",
        status="received",
        recorded_by=user.id,
        review_status="unknown",
        review_dimensions={},
    )
    db_session.add(sample)
    db_session.commit()
    assert any(
        item.code == "sample_required"
        for item in compose_build_package(db_session, organization.id, product.id).blockers
    )
    sample.status = "accepted"
    sample.review_status = "pass"
    sample.review_dimensions = {"material": "pass", "quality": "pass"}
    db_session.commit()
    assert not any(
        item.code == "sample_required"
        for item in compose_build_package(db_session, organization.id, product.id).blockers
    )


def test_candidate_promotion_is_human_confirmed_idempotent_and_tenant_safe(
    client: TestClient, db_session: Session
) -> None:
    state = build_foundation(db_session, "candidate")
    organization = state["organization"]
    user = state["user"]
    hypothesis = state["hypothesis"]
    candidate = SupplierCandidate(
        organization_id=organization.id,
        product_id=hypothesis.id,
        source_type="manufacturer",
        supplier_reference="verified:factory-001",
        estimated_cost=Decimal("10"),
        minimum_order_quantity=100,
        lead_time="30 days",
        quality_notes="Identity requires human confirmation.",
        risk_level="medium",
    )
    db_session.add(candidate)
    db_session.commit()
    payload = {
        "organization_id": str(organization.id),
        "name": "Verified Factory",
        "country": "Portugal",
    }
    first = client.post(
        f"/api/v1/supplier-candidates/{candidate.id}/promote",
        headers={"X-Actor-ID": str(user.id)},
        json=payload,
    )
    second = client.post(
        f"/api/v1/supplier-candidates/{candidate.id}/promote",
        headers={"X-Actor-ID": str(user.id)},
        json=payload,
    )
    assert first.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert (
        db_session.scalar(
            select(SupplierCandidatePromotion).where(
                SupplierCandidatePromotion.supplier_candidate_id == candidate.id
            )
        )
        is not None
    )
    other = Organization(name="Other", slug="build-other")
    db_session.add(other)
    db_session.commit()
    denied = client.post(
        f"/api/v1/supplier-candidates/{candidate.id}/promote",
        headers={"X-Actor-ID": str(user.id)},
        json={"organization_id": str(other.id), "name": "Wrong", "country": "US"},
    )
    assert denied.status_code == 404


def test_critical_product_and_supplier_risks_are_blockers(db_session: Session) -> None:
    state = build_foundation(db_session, "risk")
    organization = state["organization"]
    product = state["product"]
    supplier = state["supplier"]
    hypothesis = state["hypothesis"]
    db_session.add_all(
        [
            SupplierEvidence(
                organization_id=organization.id,
                supplier_id=supplier.id,
                field_name="material",
                value="cotton",
                classification="verified",
                source="reviewed",
                confidence=0.9,
            ),
            ProductRisk(
                organization_id=organization.id,
                product_id=hypothesis.id,
                risk_type="quality",
                severity="critical",
                description="Critical product quality risk",
                status="open",
            ),
            SupplierRisk(
                organization_id=organization.id,
                supplier_id=supplier.id,
                risk_type="quality",
                severity="critical",
                description="Critical supplier quality risk",
                status="open",
            ),
        ]
    )
    db_session.commit()
    package = compose_build_package(db_session, organization.id, product.id)
    assert {item.code for item in package.blockers} >= {
        "critical_product_risk",
        "critical_supplier_risk",
    }


def test_quote_direct_provenance_and_tenant_validation(
    client: TestClient, db_session: Session
) -> None:
    state = build_foundation(db_session, "quote-link")
    organization = state["organization"]
    quote = state["quote"]
    economics = state["economics"]
    response = client.post(
        f"/api/v1/supplier-quotes/{quote.id}/economic-provenance",
        json={
            "organization_id": str(organization.id),
            "product_economics_id": str(economics.id),
            "confidence": 0.92,
        },
    )
    assert response.status_code == 200
    assert response.json()["supplier_quote_id"] == str(quote.id)
    assert response.json()["classification"] == "quoted"

    other = Organization(name="Other Quote Tenant", slug="build-other-quote")
    db_session.add(other)
    db_session.commit()
    denied = client.post(
        f"/api/v1/supplier-quotes/{quote.id}/economic-provenance",
        json={
            "organization_id": str(other.id),
            "product_economics_id": str(economics.id),
        },
    )
    assert denied.status_code == 404


def test_sample_review_api_records_human_result_and_unknown_dimensions(
    client: TestClient, db_session: Session
) -> None:
    state = build_foundation(db_session, "sample-review")
    organization = state["organization"]
    product = state["product"]
    supplier = state["supplier"]
    relationship = state["relationship"]
    user = state["user"]
    created = client.post(
        f"/api/v1/products/{product.id}/samples",
        headers={"X-Actor-ID": str(user.id)},
        json={
            "organization_id": str(organization.id),
            "supplier_id": str(supplier.id),
            "approved_product_supplier_id": str(relationship.id),
            "sample_identifier": "SAMPLE-REVIEW",
            "status": "received",
        },
    )
    assert created.status_code == 201
    assert created.json()["review_status"] == "unknown"
    reviewed = client.post(
        f"/api/v1/samples/{created.json()['id']}/review",
        headers={"X-Actor-ID": str(user.id)},
        json={
            "organization_id": str(organization.id),
            "status": "conditional",
            "dimensions": {"material": "pass", "durability": "unknown"},
            "notes": "Durability evidence remains unknown.",
        },
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "under_review"
    assert reviewed.json()["review_dimensions"]["durability"] == "unknown"


def test_build_package_is_tenant_scoped_and_relationship_execution_is_idempotent(
    client: TestClient, db_session: Session
) -> None:
    state = build_foundation(db_session, "execution")
    organization = state["organization"]
    product = state["product"]
    supplier = state["supplier"]
    relationship = state["relationship"]
    user = state["user"]
    payload = {
        "organization_id": str(organization.id),
        "product_id": str(product.id),
        "approval_request_id": str(relationship.approval_request_id),
        "role": "primary",
    }
    first = client.post(
        f"/api/v1/suppliers/{supplier.id}/approve-for-product",
        headers={"X-Actor-ID": str(user.id)},
        json=payload,
    )
    second = client.post(
        f"/api/v1/suppliers/{supplier.id}/approve-for-product",
        headers={"X-Actor-ID": str(user.id)},
        json=payload,
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    package = client.get(
        f"/api/v1/products/{product.id}/build-package",
        params={"organization_id": str(organization.id)},
    )
    assert package.status_code == 200
    assert package.json()["origin_opportunity_id"] is not None
    other = Organization(name="Other Build Tenant", slug="build-other-package")
    db_session.add(other)
    db_session.commit()
    denied = client.get(
        f"/api/v1/products/{product.id}/build-package",
        params={"organization_id": str(other.id)},
    )
    assert denied.status_code == 404
