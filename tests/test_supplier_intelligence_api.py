from commerce_os.build.models import Product
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_supplier_intelligence_api_flow(client: TestClient, db_session: Session) -> None:
    organization = Organization(name="Supplier API", slug="supplier-api")
    db_session.add(organization)
    db_session.flush()
    brand = Brand(organization_id=organization.id, name="API Brand", slug="api-brand")
    db_session.add(brand)
    db_session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="API Product",
        description="Product",
        category="Care",
        status="approved",
    )
    db_session.add(product)
    db_session.commit()
    supplier = client.post(
        "/api/v1/suppliers",
        json={
            "organization_id": str(organization.id),
            "name": "API Factory",
            "source_type": "manual",
            "country": "Portugal",
            "capabilities": ["textiles"],
            "certifications": ["ISO 9001"],
        },
    )
    assert supplier.status_code == 201
    supplier_id = supplier.json()["id"]
    assert (
        client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            params={"organization_id": str(organization.id)},
            json={"status": "evaluating"},
        ).status_code
        == 200
    )
    evaluation = client.post(
        "/api/v1/supplier-evaluations",
        json={
            "organization_id": str(organization.id),
            "supplier_id": supplier_id,
            "quality_score": 90,
            "price_score": 70,
            "lead_time_score": 80,
            "communication_score": 85,
            "compliance_score": 95,
            "confidence_score": 0.9,
        },
    )
    assert evaluation.status_code == 201
    assert evaluation.json()["overall_score"] == 84
    assert (
        client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            params={"organization_id": str(organization.id)},
            json={"status": "approved"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/supplier-risks",
            json={
                "organization_id": str(organization.id),
                "supplier_id": supplier_id,
                "risk_type": "delivery",
                "severity": "medium",
                "description": "Seasonal delay risk",
            },
        ).status_code
        == 201
    )
    match = client.post(
        "/api/v1/product-supplier-matches",
        json={
            "organization_id": str(organization.id),
            "product_id": str(product.id),
            "supplier_id": supplier_id,
            "match_score": 82,
            "reason": "Strong product fit",
        },
    )
    assert match.status_code == 201 and match.json()["recommended"] is True
    decision = client.post(
        "/api/v1/supplier-decisions",
        json={
            "organization_id": str(organization.id),
            "product_id": str(product.id),
            "selected_supplier_id": supplier_id,
            "decision_reason": "Best evaluated fit",
            "evidence_reference": f"match:{match.json()['id']}",
        },
    )
    assert decision.status_code == 201
    for endpoint in (
        "suppliers",
        "supplier-evaluations",
        "supplier-risks",
        "product-supplier-matches",
        "supplier-decisions",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200 and len(response.json()) == 1
