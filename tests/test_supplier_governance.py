from datetime import date

from commerce_os.build.models import Product
from commerce_os.governance.models import Organization
from commerce_os.intelligence.supplier_models import (
    ProductSupplierMatch,
    SupplierEvaluation,
    SupplierProfile,
    SupplierQuote,
)
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.supplier_governance import product_supply_readiness, qualify_supplier


def foundation(session: Session, slug: str = "governed"):
    organization = Organization(name="Supplier Governance", slug=f"supplier-{slug}")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"brand-{slug}")
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Evidence Kit",
        description="A governed product.",
        category="care",
        status="draft",
    )
    supplier = SupplierProfile(
        organization_id=organization.id,
        name="Evidence Factory",
        source_type="manual",
        country="Portugal",
        capabilities=["care products"],
        certifications=[],
        status="evaluating",
    )
    session.add_all([product, supplier])
    session.flush()
    session.add_all(
        [
            ProductSupplierMatch(
                organization_id=organization.id,
                product_id=product.id,
                supplier_id=supplier.id,
                match_score=82,
                recommended=True,
                reason="Evidence-backed Product fit.",
            ),
            SupplierEvaluation(
                organization_id=organization.id,
                supplier_id=supplier.id,
                quality_score=85,
                price_score=75,
                lead_time_score=80,
                communication_score=82,
                compliance_score=78,
                overall_score=80,
                confidence_score=0.8,
                formula_version="v1.0",
            ),
            SupplierQuote(
                organization_id=organization.id,
                supplier_id=supplier.id,
                product_id=product.id,
                currency="USD",
                unit_price="12.50",
                minimum_order_quantity=100,
                price_tiers=[],
                sample_cost="20",
                tooling_cost=None,
                packaging_cost="1",
                incoterm="EXW",
                payment_terms="30% deposit; 70% before shipment",
                lead_time="30 days",
                quote_date=date.today(),
                valid_until=None,
                classification="quoted",
                source="manual quote",
                confidence=0.85,
                evidence_reference="quote:fixture",
                notes=None,
            ),
        ]
    )
    session.commit()
    return organization, product, supplier


def test_qualification_is_explainable_and_unknowns_are_not_fabricated(
    db_session: Session,
) -> None:
    organization, product, supplier = foundation(db_session)
    result = qualify_supplier(db_session, organization.id, supplier.id, product.id)
    by_name = {item.dimension: item for item in result.dimensions}
    assert result.ready is False
    assert by_name["product_fit"].status == "pass"
    assert by_name["commercial_fit"].status == "pass"
    assert by_name["capacity"].status == "unknown"
    assert by_name["capacity"].confidence is None
    assert any(item.code == "unknown_capacity" for item in result.readiness)
    assert any(item.code == "product_truth" for item in result.readiness)


def test_legacy_direct_product_is_not_supply_ready(db_session: Session) -> None:
    organization, product, _supplier = foundation(db_session, "legacy")
    result = product_supply_readiness(db_session, organization.id, product.id)
    assert result.ready is False
    assert (
        next(item for item in result.items if item.code == "governed_product_origin").status
        == "blocked"
    )
    assert (
        next(item for item in result.items if item.code == "approved_supplier").status == "blocked"
    )


def test_supplier_evidence_and_quote_apis_preserve_tenant_scope(
    client: TestClient, db_session: Session
) -> None:
    organization, product, supplier = foundation(db_session, "api")
    payload = {
        "organization_id": str(organization.id),
        "supplier_id": str(supplier.id),
        "field_name": "production_capacity",
        "value": {"monthly_units": 5000},
        "classification": "supplier_claimed",
        "source": "supplier questionnaire",
        "confidence": 0.6,
    }
    created = client.post("/api/v1/supplier-evidence", json=payload)
    assert created.status_code == 201
    assert created.json()["classification"] == "supplier_claimed"
    listed = client.get(
        "/api/v1/supplier-evidence",
        params={"organization_id": str(organization.id), "supplier_id": str(supplier.id)},
    )
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]
    qualification = client.get(
        f"/api/v1/suppliers/{supplier.id}/qualification",
        params={"organization_id": str(organization.id), "product_id": str(product.id)},
    )
    assert qualification.status_code == 200
    assert qualification.json()["supplier_id"] == str(supplier.id)


def test_supplier_quote_rejects_invalid_confidence(client: TestClient, db_session: Session) -> None:
    organization, product, supplier = foundation(db_session, "quote")
    response = client.post(
        "/api/v1/supplier-quotes",
        json={
            "organization_id": str(organization.id),
            "supplier_id": str(supplier.id),
            "product_id": str(product.id),
            "currency": "USD",
            "unit_price": "9.50",
            "minimum_order_quantity": 50,
            "quote_date": str(date.today()),
            "classification": "quoted",
            "source": "manual quote",
            "confidence": 1.5,
        },
    )
    assert response.status_code == 422
