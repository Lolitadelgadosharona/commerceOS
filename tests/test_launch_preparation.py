import pytest
from commerce_os.build.listing_models import ListingStrategy
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeStrategy
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.decision.launch_schemas import LaunchPackageCreate
from commerce_os.decision.launch_services import LaunchPreparationService
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.operations.execution_models import ProductLaunch
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def product_foundation(
    session: Session, slug: str, status: str = "approved"
) -> tuple[Organization, Product]:
    organization = Organization(name=f"Launch {slug}", slug=f"launch-{slug}")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name=f"Brand {slug}", slug=f"brand-{slug}")
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Prepared product",
        description="Approved Build product",
        category="home",
        status=status,
    )
    session.add(product)
    session.commit()
    return organization, product


def test_launch_package_readiness_evidence_and_no_execution(
    client: TestClient, db_session: Session
) -> None:
    organization, product = product_foundation(db_session, "api")
    base = {"organization_id": str(organization.id), "product_id": str(product.id)}
    positioning = client.post(
        "/api/v1/product-positioning",
        json=base
        | {
            "target_customer": "Apartment dwellers",
            "customer_problem": "Noisy cooling",
            "primary_benefit": "Quiet comfort",
            "differentiation": "Evidence-backed low-noise design",
            "positioning_statement": "Quiet cooling for compact homes",
            "confidence": 0.8,
        },
    )
    assert positioning.status_code == 201
    offer = client.post(
        "/api/v1/offer-strategies",
        json=base
        | {
            "pricing_hypothesis": "Test a premium supported by quiet operation",
            "bundle_strategy": "Optional care bundle",
            "guarantee_strategy": "Owner review required before any guarantee",
            "bonus_strategy": "No bonus in foundation",
            "urgency_strategy": "No artificial urgency",
            "confidence": 0.6,
        },
    )
    assert offer.status_code == 201
    objection = client.post(
        "/api/v1/product-objections",
        json=base
        | {
            "objection_type": "price",
            "customer_language": "Why does this cost more?",
            "recommended_response": "Explain verified differentiation without unsupported claims.",
            "evidence_reference": "internal://customer-language/price-1",
        },
    )
    assert objection.status_code == 201
    assert objection.json()["evidence_reference"] == "internal://customer-language/price-1"
    db_session.add_all(
        [
            CreativeStrategy(
                organization_id=organization.id,
                product_id=product.id,
                target_audience="Apartment dwellers",
                marketing_objective="Prepare evidence",
                core_message="Quiet comfort",
                emotional_angle="Relief",
                creative_direction="Evidence first",
                status="approved",
            ),
            ListingStrategy(
                organization_id=organization.id,
                product_id=product.id,
                target_customer="Apartment dwellers",
                value_proposition="Quiet comfort",
                positioning="Premium quiet cooling",
                differentiation="Verified low-noise design",
                status="active",
            ),
        ]
    )
    db_session.commit()
    package = client.post("/api/v1/launch-packages", json=base)
    assert package.status_code == 201
    expected = {
        "positioning_status": "ready",
        "offer_status": "review",
        "objection_status": "ready",
        "creative_readiness": "ready",
        "listing_readiness": "ready",
        "launch_score": 90.0,
    }
    assert {field: package.json()[field] for field in expected} == expected
    db_session.refresh(product)
    assert product.status == "approved"
    assert db_session.scalar(select(func.count()).select_from(ProductLaunch)) == 0
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    for endpoint in (
        "product-positioning",
        "offer-strategies",
        "product-objections",
        "launch-packages",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200
        assert response.json()


def test_tenant_boundary_product_gate_and_no_execution_route(
    client: TestClient, db_session: Session
) -> None:
    owner, product = product_foundation(db_session, "owner")
    other, _ = product_foundation(db_session, "other")
    _, draft = product_foundation(db_session, "draft", status="draft")
    with pytest.raises(DecisionScopeError):
        LaunchPreparationService(db_session).prepare_package(
            LaunchPackageCreate(organization_id=other.id, product_id=product.id)
        )
    blocked = client.post(
        "/api/v1/launch-packages",
        json={"organization_id": str(draft.organization_id), "product_id": str(draft.id)},
    )
    assert blocked.status_code == 409
    empty = client.post(
        "/api/v1/launch-packages",
        json={"organization_id": str(owner.id), "product_id": str(product.id)},
    )
    assert empty.status_code == 201
    assert empty.json()["launch_score"] == 0
    assert client.post("/api/v1/launch-packages/execute", json={}).status_code in {404, 405, 422}
