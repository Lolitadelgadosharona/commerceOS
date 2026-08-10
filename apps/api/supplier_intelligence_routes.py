from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.intelligence.errors import IntelligenceNotFoundError
from commerce_os.intelligence.supplier_models import (
    ProductSupplierMatch,
    SupplierDecisionRecord,
    SupplierEvaluation,
    SupplierProfile,
    SupplierProfileStatus,
    SupplierRisk,
)
from commerce_os.intelligence.supplier_schemas import (
    ProductSupplierMatchCreate,
    ProductSupplierMatchRead,
    SupplierDecisionCreate,
    SupplierDecisionRead,
    SupplierEvaluationCreate,
    SupplierEvaluationRead,
    SupplierProfileCreate,
    SupplierProfileRead,
    SupplierProfileUpdate,
    SupplierRiskCreate,
    SupplierRiskRead,
)
from commerce_os.intelligence.supplier_services import (
    ProductSupplierMatchService,
    SupplierDecisionService,
    SupplierEvaluationService,
    SupplierProfileService,
    SupplierRiskService,
    get_scoped_supplier,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _get(session: Session, model: type[ModelT], entity_id: UUID) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise IntelligenceNotFoundError("Supplier intelligence resource was not found.")
    return entity


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post("/suppliers", response_model=SupplierProfileRead, status_code=201, tags=["suppliers"])
def create_supplier(payload: SupplierProfileCreate, session: SessionDependency) -> SupplierProfile:
    return SupplierProfileService(session).create(payload)


@router.get("/suppliers", response_model=list[SupplierProfileRead], tags=["suppliers"])
def list_suppliers(organization_id: UUID, session: SessionDependency) -> list[SupplierProfile]:
    return _list(session, SupplierProfile, organization_id)


@router.get("/suppliers/{supplier_id}", response_model=SupplierProfileRead, tags=["suppliers"])
def get_supplier(
    supplier_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierProfile:
    return get_scoped_supplier(session, supplier_id, organization_id)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierProfileRead, tags=["suppliers"])
def transition_supplier(
    supplier_id: UUID,
    organization_id: UUID,
    payload: SupplierProfileUpdate,
    session: SessionDependency,
) -> SupplierProfile:
    supplier = get_scoped_supplier(session, supplier_id, organization_id)
    return SupplierProfileService(session).transition(
        supplier, SupplierProfileStatus(payload.status)
    )


@router.post(
    "/supplier-evaluations",
    response_model=SupplierEvaluationRead,
    status_code=201,
    tags=["supplier_evaluations"],
)
def create_evaluation(
    payload: SupplierEvaluationCreate, session: SessionDependency
) -> SupplierEvaluation:
    return SupplierEvaluationService(session).create(payload)


@router.get(
    "/supplier-evaluations",
    response_model=list[SupplierEvaluationRead],
    tags=["supplier_evaluations"],
)
def list_evaluations(organization_id: UUID, session: SessionDependency) -> list[SupplierEvaluation]:
    return _list(session, SupplierEvaluation, organization_id)


@router.post(
    "/supplier-risks", response_model=SupplierRiskRead, status_code=201, tags=["supplier_risks"]
)
def create_risk(payload: SupplierRiskCreate, session: SessionDependency) -> SupplierRisk:
    return SupplierRiskService(session).create(payload)


@router.get("/supplier-risks", response_model=list[SupplierRiskRead], tags=["supplier_risks"])
def list_risks(organization_id: UUID, session: SessionDependency) -> list[SupplierRisk]:
    return _list(session, SupplierRisk, organization_id)


@router.post(
    "/product-supplier-matches",
    response_model=ProductSupplierMatchRead,
    status_code=201,
    tags=["product_supplier_matches"],
)
def create_match(
    payload: ProductSupplierMatchCreate, session: SessionDependency
) -> ProductSupplierMatch:
    return ProductSupplierMatchService(session).create(payload)


@router.get(
    "/product-supplier-matches",
    response_model=list[ProductSupplierMatchRead],
    tags=["product_supplier_matches"],
)
def list_matches(organization_id: UUID, session: SessionDependency) -> list[ProductSupplierMatch]:
    return _list(session, ProductSupplierMatch, organization_id)


@router.post(
    "/supplier-decisions",
    response_model=SupplierDecisionRead,
    status_code=201,
    tags=["supplier_decisions"],
)
def create_decision(
    payload: SupplierDecisionCreate, session: SessionDependency
) -> SupplierDecisionRecord:
    return SupplierDecisionService(session).create(payload)


@router.get(
    "/supplier-decisions", response_model=list[SupplierDecisionRead], tags=["supplier_decisions"]
)
def list_decisions(
    organization_id: UUID, session: SessionDependency
) -> list[SupplierDecisionRecord]:
    return _list(session, SupplierDecisionRecord, organization_id)
