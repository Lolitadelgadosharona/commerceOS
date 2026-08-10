import pytest
from commerce_os.build.errors import BuildStateError
from commerce_os.build.models import Product, ProductKnowledgeItem, ProductStatus
from commerce_os.build.schemas import (
    ProductClaimPolicyCreate,
    ProductCreate,
    ProductKnowledgeItemCreate,
    ProductKnowledgeItemUpdate,
)
from commerce_os.build.services import (
    ProductClaimPolicyService,
    ProductKnowledgeService,
    ProductService,
)
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from sqlalchemy.orm import Session


def foundation(session: Session) -> tuple[Organization, Brand]:
    organization = Organization(name="Truth Test", slug="truth-test")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Trusted Brand", slug="trusted-brand")
    session.add(brand)
    session.commit()
    return organization, brand


def test_product_lifecycle_requires_approved_truth(db_session: Session) -> None:
    organization, brand = foundation(db_session)
    product = ProductService(db_session).create(
        ProductCreate(
            organization_id=organization.id,
            brand_id=brand.id,
            name="Care Kit",
            description="Approved care product",
            category="Care",
        )
    )
    assert product.status == "draft"
    with pytest.raises(BuildStateError):
        ProductService(db_session).transition(product, status=ProductStatus.ACTIVE)


def test_knowledge_is_versioned_and_claim_policy_is_brand_scoped(db_session: Session) -> None:
    organization, brand = foundation(db_session)
    product = ProductService(db_session).create(
        ProductCreate(
            organization_id=organization.id,
            brand_id=brand.id,
            name="Care Kit",
            description="Approved care product",
            category="Care",
        )
    )
    service = ProductKnowledgeService(db_session)
    item = service.create(
        ProductKnowledgeItemCreate(
            organization_id=organization.id,
            product_id=product.id,
            type="care_instruction",
            content="Hand wash.",
            confidence=0.8,
        )
    )
    assert item.version == 1
    service.update(
        item,
        ProductKnowledgeItemUpdate(
            content="Hand wash in cool water.", confidence=0.95, approval_status="approved"
        ),
    )
    assert item.version == 2
    policy = ProductClaimPolicyService(db_session).create(
        ProductClaimPolicyCreate(
            organization_id=organization.id,
            brand_id=brand.id,
            claim_type="medical",
            allowed=False,
            reason="Medical claims require legal review.",
            evidence_required=True,
        )
    )
    assert policy.allowed is False
    assert policy.evidence_required is True
    assert Product.__tablename__ == "products"
    assert ProductKnowledgeItem.__tablename__ == "product_knowledge_items"
