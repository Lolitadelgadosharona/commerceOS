from uuid import uuid4

from commerce_os.build.models import Product, ProductTruth
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_listing_intelligence_api_flow(client: TestClient, db_session: Session) -> None:
    organization = Organization(name="Listing API", slug="listing-api")
    db_session.add(organization)
    db_session.flush()
    brand = Brand(organization_id=organization.id, name="Listing Brand", slug="listing-brand")
    db_session.add(brand)
    db_session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Product",
        category="Care",
        status="approved",
    )
    db_session.add(product)
    db_session.flush()
    truth = ProductTruth(
        organization_id=organization.id,
        product_id=product.id,
        version=1,
        summary="Verified",
        features=["Reusable"],
        specifications={"material": "cotton"},
        approved_claims=["Reusable"],
        restricted_claims=[],
        usage_notes="Follow instructions",
        created_by=uuid4(),
        approval_id=uuid4(),
    )
    db_session.add(truth)
    db_session.commit()
    base = {"organization_id": str(organization.id), "product_id": str(product.id)}
    strategy = client.post(
        "/api/v1/listing-strategies",
        json=base
        | {
            "target_customer": "Care-focused households",
            "value_proposition": "Trusted reusable care",
            "positioning": "Evidence-first",
            "differentiation": "Verified facts",
        },
    )
    assert strategy.status_code == 201
    assert (
        client.patch(
            f"/api/v1/listing-strategies/{strategy.json()['id']}",
            params={"organization_id": str(organization.id)},
            json={"status": "approved"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/customer-questions",
            json=base
            | {
                "question": "How is quality verified?",
                "question_type": "quality",
                "source_reference": "customer-signal:manual",
                "importance_score": 90,
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/product-discovery-knowledge",
            json=base
            | {
                "entity_type": "use_case",
                "entity_name": "Home care",
                "description": "Reusable home care",
                "relationship": "supported_by_product",
                "confidence_score": 0.9,
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/content-briefs",
            json=base
            | {
                "headline_direction": "Lead with verified utility",
                "key_benefits": ["Reusable"],
                "proof_points": ["Cotton specification"],
                "objections": ["Quality"],
                "trust_elements": ["Product Truth"],
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/listing-evidence",
            json=base
            | {
                "evidence_type": "specification",
                "source_reference": str(truth.id),
                "content": "Cotton material",
                "confidence_score": 1,
            },
        ).status_code
        == 201
    )
    for endpoint in (
        "listing-strategies",
        "customer-questions",
        "product-discovery-knowledge",
        "content-briefs",
        "listing-evidence",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200 and len(response.json()) == 1
