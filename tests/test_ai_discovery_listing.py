import pytest
from commerce_os.build.listing_models import ListingStrategy
from commerce_os.build.models import Product, ProductTruth
from commerce_os.decision.discovery_listing_schemas import ListingAssessmentCreate
from commerce_os.decision.discovery_listing_services import DiscoveryListingService
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.decision.launch_models import ProductObjectionMap
from commerce_os.governance.models import ApprovalRequest, Organization, User
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def product_truth_foundation(
    session: Session, slug: str, status: str = "approved"
) -> tuple[Organization, Product, ProductTruth]:
    organization = Organization(name=f"Discovery {slug}", slug=f"discovery-{slug}")
    session.add(organization)
    session.flush()
    user = User(
        organization_id=organization.id,
        email=f"owner-{slug}@example.com",
        display_name="Owner",
        status="active",
        principal_type="human",
    )
    brand = Brand(organization_id=organization.id, name=f"Brand {slug}", slug=f"brand-{slug}")
    session.add_all([user, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Discovery product",
        description="Approved Build product",
        category="home",
        status=status,
    )
    session.add(product)
    session.flush()
    approval = ApprovalRequest(
        organization_id=organization.id,
        requester_id=user.id,
        object_type="product",
        object_id=product.id,
        requested_action="approve_product_truth",
        reason="Test foundation",
        status="approved",
        approver_id=user.id,
    )
    session.add(approval)
    session.flush()
    truth = ProductTruth(
        organization_id=organization.id,
        product_id=product.id,
        version=1,
        summary="A quiet cooling product.",
        features=["Low-noise operation"],
        specifications={"noise": "verified specification"},
        approved_claims=["Designed for quiet operation"],
        restricted_claims=["Medical benefit"],
        usage_notes="Follow the approved instructions.",
        created_by=user.id,
        approval_id=approval.id,
    )
    session.add(truth)
    session.commit()
    return organization, product, truth


def test_geo_quality_discovery_and_truth_immutability(
    client: TestClient, db_session: Session
) -> None:
    organization, product, truth = product_truth_foundation(db_session, "api")
    base = {"organization_id": str(organization.id), "product_id": str(product.id)}
    blueprint = client.post(
        "/api/v1/listing-blueprints",
        json=base
        | {
            "title_strategy": "Lead with the verified product entity and primary benefit.",
            "benefit_structure": ["Quiet comfort"],
            "feature_structure": ["Low-noise operation"],
            "faq_structure": ["What evidence supports the noise claim?"],
            "trust_elements": ["Approved Product Truth claim"],
            "comparison_points": ["Compare verified noise specifications"],
            "confidence": 0.85,
        },
    )
    assert blueprint.status_code == 201
    geo = client.post(
        "/api/v1/geo-assets",
        json=base
        | {
            "entity_description": "A compact cooling product designed for quiet operation.",
            "attributes": {"category": "cooling", "audience": "apartment dwellers"},
            "use_cases": ["Quiet home cooling"],
            "customer_questions": ["How quiet is it?"],
            "answer_structure": {"direct_answer": "Use approved evidence only"},
            "evidence_reference": "internal://product-truth/version-1",
        },
    )
    assert geo.status_code == 201
    assert geo.json()["evidence_reference"] == "internal://product-truth/version-1"
    for index in range(3):
        db_session.add(
            ProductObjectionMap(
                organization_id=organization.id,
                product_id=product.id,
                objection_type="trust",
                customer_language=f"How do I know this is true? {index}",
                recommended_response="Use approved evidence.",
                evidence_reference=f"internal://customer-language/{index}",
            )
        )
    db_session.commit()
    quality = client.post("/api/v1/listing-quality-assessments", json=base)
    assert quality.status_code == 201
    expected = {
        "truth_score": 100.0,
        "customer_language_score": 75.0,
        "geo_score": 100.0,
        "trust_score": 100.0,
        "conversion_score": 100.0,
        "overall_score": 95.0,
    }
    assert {field: quality.json()[field] for field in expected} == expected
    discovery = client.post("/api/v1/ai-discovery-readiness", json=base)
    assert discovery.status_code == 201
    assert discovery.json()["coverage_score"] == 95.0
    assert discovery.json()["missing_information"] == []
    assert discovery.json()["recommendation"] == "ready_for_human_review"
    db_session.refresh(truth)
    assert truth.version == 1
    assert truth.summary == "A quiet cooling product."
    assert db_session.scalar(select(func.count()).select_from(ListingStrategy)) == 0
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 1
    for endpoint in (
        "listing-blueprints",
        "geo-assets",
        "listing-quality-assessments",
        "ai-discovery-readiness",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200
        assert response.json()


def test_tenant_product_gate_missing_information_and_no_publish(
    client: TestClient, db_session: Session
) -> None:
    owner, product, _ = product_truth_foundation(db_session, "owner")
    other, _, _ = product_truth_foundation(db_session, "other")
    _, draft, _ = product_truth_foundation(db_session, "draft", status="draft")
    with pytest.raises(DecisionScopeError):
        DiscoveryListingService(db_session).assess_quality(
            ListingAssessmentCreate(organization_id=other.id, product_id=product.id)
        )
    blocked = client.post(
        "/api/v1/listing-quality-assessments",
        json={"organization_id": str(draft.organization_id), "product_id": str(draft.id)},
    )
    assert blocked.status_code == 409
    quality = client.post(
        "/api/v1/listing-quality-assessments",
        json={"organization_id": str(owner.id), "product_id": str(product.id)},
    )
    assert quality.status_code == 201
    readiness = client.post(
        "/api/v1/ai-discovery-readiness",
        json={"organization_id": str(owner.id), "product_id": str(product.id)},
    )
    assert readiness.status_code == 201
    assert "geo_knowledge" in readiness.json()["missing_information"]
    assert readiness.json()["recommendation"] == "insufficient_evidence"
    assert client.post("/api/v1/listing-blueprints/publish", json={}).status_code in {
        404,
        405,
        422,
    }
