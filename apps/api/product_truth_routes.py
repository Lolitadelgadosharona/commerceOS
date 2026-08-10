from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.build.errors import BuildNotFoundError, BuildScopeError, BuildStateError
from commerce_os.build.models import (
    Product,
    ProductClaimPolicy,
    ProductKnowledgeItem,
    ProductStatus,
    ProductTruth,
)
from commerce_os.build.schemas import (
    ProductApprovalRequest,
    ProductClaimPolicyCreate,
    ProductClaimPolicyRead,
    ProductCreate,
    ProductKnowledgeItemCreate,
    ProductKnowledgeItemRead,
    ProductKnowledgeItemUpdate,
    ProductRead,
    ProductTruthCreate,
    ProductTruthRead,
    ProductUpdate,
)
from commerce_os.build.services import (
    ProductClaimPolicyService,
    ProductKnowledgeService,
    ProductService,
    ProductTruthService,
    get_scoped_product,
)
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    PrincipalType,
    User,
    UserStatus,
)
from commerce_os.governance.schemas import ApprovalRequestRead
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ActorDependency = Annotated[UUID, Header(alias="X-Actor-ID")]
ModelT = TypeVar("ModelT", bound=Base)


def _get_scoped(
    session: Session, model: type[ModelT], entity_id: UUID, organization_id: UUID
) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise BuildNotFoundError("The requested product resource was not found.")
    if entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise BuildScopeError("The requested product resource belongs to another organization.")
    return entity


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post("/products", response_model=ProductRead, status_code=201, tags=["products"])
def create_product(payload: ProductCreate, session: SessionDependency) -> Product:
    return ProductService(session).create(payload)


@router.get("/products", response_model=list[ProductRead], tags=["products"])
def list_products(organization_id: UUID, session: SessionDependency) -> list[Product]:
    return _list(session, Product, organization_id)


@router.get("/products/{product_id}", response_model=ProductRead, tags=["products"])
def get_product(product_id: UUID, organization_id: UUID, session: SessionDependency) -> Product:
    return get_scoped_product(session, product_id, organization_id)


@router.patch("/products/{product_id}", response_model=ProductRead, tags=["products"])
def transition_product(
    product_id: UUID, organization_id: UUID, payload: ProductUpdate, session: SessionDependency
) -> Product:
    product = get_scoped_product(session, product_id, organization_id)
    return ProductService(session).transition(product, ProductStatus(payload.status))


@router.post(
    "/products/{product_id}/approval",
    response_model=ApprovalRequestRead,
    status_code=201,
    tags=["products"],
)
def request_product_approval(
    product_id: UUID,
    organization_id: UUID,
    payload: ProductApprovalRequest,
    actor: ActorDependency,
    session: SessionDependency,
) -> ApprovalRequest:
    get_scoped_product(session, product_id, organization_id)
    return ApprovalWorkflowService(session).request(
        organization_id=organization_id,
        project_id=None,
        requester_id=actor,
        object_type="product",
        object_id=product_id,
        requested_action="product_truth.publish",
        reason=payload.reason,
    )


@router.post(
    "/product-truth", response_model=ProductTruthRead, status_code=201, tags=["product_truth"]
)
def create_product_truth(
    payload: ProductTruthCreate, actor: ActorDependency, session: SessionDependency
) -> ProductTruth:
    publisher = session.get(User, actor)
    if (
        publisher is None
        or publisher.organization_id != payload.organization_id
        or publisher.status != UserStatus.ACTIVE
        or publisher.principal_type != PrincipalType.HUMAN
    ):
        raise BuildScopeError("Only an active in-scope human may publish Product Truth.")
    approval = session.get(ApprovalRequest, payload.approval_id)
    if approval is None:
        raise BuildNotFoundError("Product approval request was not found.")
    if (
        approval.organization_id != payload.organization_id
        or approval.object_type != "product"
        or approval.object_id != payload.product_id
        or approval.requested_action != "product_truth.publish"
    ):
        raise BuildScopeError("Approval request does not authorize this Product Truth.")
    if approval.status != ApprovalStatus.APPROVED or approval.approver_id is None:
        raise BuildStateError("An approved product publication request is required.")
    product, truth = ProductTruthService(session).finalize(payload, created_by=actor)
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor,
        action="product_truth.created",
        entity_type="product_truth",
        entity_id=truth.id,
        metadata={
            "product_id": str(product.id),
            "truth_version": truth.version,
            "approval_id": str(approval.id),
        },
    )
    session.commit()
    session.refresh(truth)
    return truth


@router.get("/product-truth", response_model=list[ProductTruthRead], tags=["product_truth"])
def list_product_truth(organization_id: UUID, session: SessionDependency) -> list[ProductTruth]:
    return _list(session, ProductTruth, organization_id)


@router.get("/product-truth/{truth_id}", response_model=ProductTruthRead, tags=["product_truth"])
def get_product_truth(
    truth_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProductTruth:
    return _get_scoped(session, ProductTruth, truth_id, organization_id)


@router.post(
    "/product-knowledge",
    response_model=ProductKnowledgeItemRead,
    status_code=201,
    tags=["product_knowledge"],
)
def create_product_knowledge(
    payload: ProductKnowledgeItemCreate, session: SessionDependency
) -> ProductKnowledgeItem:
    return ProductKnowledgeService(session).create(payload)


@router.get(
    "/product-knowledge", response_model=list[ProductKnowledgeItemRead], tags=["product_knowledge"]
)
def list_product_knowledge(
    organization_id: UUID, session: SessionDependency
) -> list[ProductKnowledgeItem]:
    return _list(session, ProductKnowledgeItem, organization_id)


@router.patch(
    "/product-knowledge/{item_id}",
    response_model=ProductKnowledgeItemRead,
    tags=["product_knowledge"],
)
def update_product_knowledge(
    item_id: UUID,
    organization_id: UUID,
    payload: ProductKnowledgeItemUpdate,
    session: SessionDependency,
) -> ProductKnowledgeItem:
    item = _get_scoped(session, ProductKnowledgeItem, item_id, organization_id)
    return ProductKnowledgeService(session).update(item, payload)


@router.post(
    "/product-claim-policies",
    response_model=ProductClaimPolicyRead,
    status_code=201,
    tags=["product_claim_policies"],
)
def create_claim_policy(
    payload: ProductClaimPolicyCreate, session: SessionDependency
) -> ProductClaimPolicy:
    return ProductClaimPolicyService(session).create(payload)


@router.get(
    "/product-claim-policies",
    response_model=list[ProductClaimPolicyRead],
    tags=["product_claim_policies"],
)
def list_claim_policies(
    organization_id: UUID, session: SessionDependency
) -> list[ProductClaimPolicy]:
    return _list(session, ProductClaimPolicy, organization_id)
