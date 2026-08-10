from uuid import uuid4

import pytest
from commerce_os.build.errors import BuildScopeError
from commerce_os.build.listing_models import ListingStrategyStatus
from commerce_os.build.listing_schemas import ListingEvidenceCreate, ListingStrategyCreate
from commerce_os.build.listing_services import ListingKnowledgeService, ListingStrategyService
from commerce_os.build.models import Product, ProductTruth
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from sqlalchemy.orm import Session


def foundation(
    session: Session, slug: str = "listing-test"
) -> tuple[Organization, Product, ProductTruth]:
    organization = Organization(name=slug, slug=slug)
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name=slug, slug=slug)
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
    session.flush()
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
    session.add(truth)
    session.commit()
    return organization, product, truth


def test_listing_strategy_lifecycle_and_evidence_relationship(db_session: Session) -> None:
    organization, product, truth = foundation(db_session)
    strategy = ListingStrategyService(db_session).create(
        ListingStrategyCreate(
            organization_id=organization.id,
            product_id=product.id,
            target_customer="Care-focused households",
            value_proposition="Trusted reusable care",
            positioning="Evidence-first",
            differentiation="Verified product facts",
        )
    )
    assert strategy.status == "draft"
    ListingStrategyService(db_session).transition(strategy, ListingStrategyStatus.APPROVED)
    ListingStrategyService(db_session).transition(strategy, ListingStrategyStatus.ACTIVE)
    assert strategy.status == "active"
    evidence = ListingKnowledgeService(db_session).create_evidence(
        ListingEvidenceCreate(
            organization_id=organization.id,
            product_id=product.id,
            evidence_type="specification",
            source_reference=str(truth.id),
            content="Cotton material",
            confidence_score=1,
        )
    )
    assert evidence.product_id == product.id
    other_org, other_product, _ = foundation(db_session, "listing-other")
    with pytest.raises(BuildScopeError):
        ListingKnowledgeService(db_session).create_evidence(
            ListingEvidenceCreate(
                organization_id=other_org.id,
                product_id=other_product.id,
                evidence_type="specification",
                source_reference=str(truth.id),
                content="Wrong product",
                confidence_score=1,
            )
        )
