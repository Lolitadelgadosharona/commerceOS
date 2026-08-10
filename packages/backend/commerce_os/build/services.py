from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.build.errors import BuildNotFoundError, BuildScopeError, BuildStateError
from commerce_os.build.models import (
    Product,
    ProductClaimPolicy,
    ProductKnowledgeItem,
    ProductStatus,
    ProductTruth,
)
from commerce_os.build.schemas import (
    ProductClaimPolicyCreate,
    ProductCreate,
    ProductKnowledgeItemCreate,
    ProductKnowledgeItemUpdate,
    ProductTruthCreate,
)
from commerce_os.shared.scope import reference_belongs_to_organization


def get_scoped_product(session: Session, product_id: UUID, organization_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None:
        raise BuildNotFoundError("Product was not found.")
    if product.organization_id != organization_id:
        raise BuildScopeError("Product belongs to another organization.")
    return product


class ProductService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductCreate) -> Product:
        if not reference_belongs_to_organization(
            self.session,
            table_name="brands",
            reference_id=payload.brand_id,
            organization_id=payload.organization_id,
        ):
            raise BuildScopeError("Brand was not found in this organization.")
        product = Product(**payload.model_dump(), status=ProductStatus.DRAFT)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def transition(self, product: Product, status: ProductStatus) -> Product:
        if status == ProductStatus.APPROVED or status == ProductStatus.DRAFT:
            raise BuildStateError(
                "Approval state can only be changed through the approval workflow."
            )
        if product.status == ProductStatus.ARCHIVED:
            raise BuildStateError("Archived products cannot transition.")
        if status == ProductStatus.ACTIVE:
            if product.status != ProductStatus.APPROVED:
                raise BuildStateError("Only approved products can become active.")
            truth_exists = self.session.scalar(
                select(ProductTruth.id).where(ProductTruth.product_id == product.id).limit(1)
            )
            if truth_exists is None:
                raise BuildStateError("An approved Product Truth is required before activation.")
        product.status = status
        self.session.commit()
        self.session.refresh(product)
        return product


class ProductTruthService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def finalize(
        self, payload: ProductTruthCreate, *, created_by: UUID
    ) -> tuple[Product, ProductTruth]:
        product = get_scoped_product(self.session, payload.product_id, payload.organization_id)
        latest = (
            self.session.scalar(
                select(func.max(ProductTruth.version)).where(ProductTruth.product_id == product.id)
            )
            or 0
        )
        truth = ProductTruth(
            **payload.model_dump(exclude={"approval_id"}),
            approval_id=payload.approval_id,
            created_by=created_by,
            version=latest + 1,
        )
        self.session.add(truth)
        if product.status == ProductStatus.DRAFT:
            product.status = ProductStatus.APPROVED
        self.session.flush()
        return product, truth


class ProductKnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductKnowledgeItemCreate) -> ProductKnowledgeItem:
        get_scoped_product(self.session, payload.product_id, payload.organization_id)
        item = ProductKnowledgeItem(**payload.model_dump())
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(
        self, item: ProductKnowledgeItem, payload: ProductKnowledgeItemUpdate
    ) -> ProductKnowledgeItem:
        for field, value in payload.model_dump().items():
            setattr(item, field, value)
        self.session.commit()
        self.session.refresh(item)
        return item


class ProductClaimPolicyService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductClaimPolicyCreate) -> ProductClaimPolicy:
        if not reference_belongs_to_organization(
            self.session,
            table_name="brands",
            reference_id=payload.brand_id,
            organization_id=payload.organization_id,
        ):
            raise BuildScopeError("Brand was not found in this organization.")
        policy = ProductClaimPolicy(**payload.model_dump())
        self.session.add(policy)
        self.session.commit()
        self.session.refresh(policy)
        return policy
