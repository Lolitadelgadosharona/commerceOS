import pytest
from commerce_os.build.models import Product
from commerce_os.governance.models import Organization
from commerce_os.intelligence.errors import IntelligenceValidationError
from commerce_os.intelligence.supplier_models import SupplierProfileStatus
from commerce_os.intelligence.supplier_schemas import (
    ProductSupplierMatchCreate,
    SupplierDecisionCreate,
    SupplierEvaluationCreate,
    SupplierProfileCreate,
    SupplierRiskCreate,
)
from commerce_os.intelligence.supplier_services import (
    ProductSupplierMatchService,
    SupplierDecisionService,
    SupplierEvaluationService,
    SupplierProfileService,
    SupplierRiskService,
)
from commerce_os.operations.models import Brand
from sqlalchemy.orm import Session


def foundation(session: Session) -> tuple[Organization, Product]:
    organization = Organization(name="Supplier Test", slug="supplier-test")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Brand", slug="brand")
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Product",
        category="Care",
        status="approved",
    )
    session.add(product)
    session.commit()
    return organization, product


def test_supplier_lifecycle_scoring_risk_matching_and_decision(db_session: Session) -> None:
    organization, product = foundation(db_session)
    profiles = SupplierProfileService(db_session)
    supplier = profiles.create(
        SupplierProfileCreate(
            organization_id=organization.id,
            name="Example Factory",
            source_type="manual",
            country="Portugal",
            capabilities=["textiles"],
            certifications=["ISO 9001"],
        )
    )
    assert supplier.status == "discovered"
    with pytest.raises(IntelligenceValidationError):
        profiles.transition(supplier, SupplierProfileStatus.APPROVED)
    profiles.transition(supplier, SupplierProfileStatus.EVALUATING)
    evaluation = SupplierEvaluationService(db_session).create(
        SupplierEvaluationCreate(
            organization_id=organization.id,
            supplier_id=supplier.id,
            quality_score=90,
            price_score=70,
            lead_time_score=80,
            communication_score=85,
            compliance_score=95,
            confidence_score=0.9,
        )
    )
    assert evaluation.overall_score == 84
    profiles.transition(supplier, SupplierProfileStatus.APPROVED)
    risk = SupplierRiskService(db_session).create(
        SupplierRiskCreate(
            organization_id=organization.id,
            supplier_id=supplier.id,
            risk_type="capacity",
            severity="medium",
            description="Seasonal capacity constraint",
        )
    )
    assert risk.risk_type == "capacity"
    match = ProductSupplierMatchService(db_session).create(
        ProductSupplierMatchCreate(
            organization_id=organization.id,
            product_id=product.id,
            supplier_id=supplier.id,
            match_score=82,
            reason="Capability and quality fit",
        )
    )
    assert match.recommended is True
    decision = SupplierDecisionService(db_session).create(
        SupplierDecisionCreate(
            organization_id=organization.id,
            product_id=product.id,
            selected_supplier_id=supplier.id,
            decision_reason="Best evaluated fit",
            evidence_reference=f"match:{match.id}",
        )
    )
    assert decision.selected_supplier_id == supplier.id
