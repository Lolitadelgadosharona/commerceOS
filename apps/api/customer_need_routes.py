from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.need_models import (
    CustomerBackedOpportunityAssessment,
    CustomerNeed,
    PainNeedMapping,
    ProductSolutionHypothesis,
)
from commerce_os.intelligence.need_schemas import (
    CustomerBackedAssessmentCreate,
    CustomerBackedAssessmentRead,
    CustomerNeedCreate,
    CustomerNeedRead,
    CustomerNeedUpdate,
    PainNeedMappingCreate,
    PainNeedMappingRead,
    ProductSolutionCreate,
    ProductSolutionRead,
)
from commerce_os.intelligence.need_services import CustomerNeedService, scoped_need
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/customer-needs", response_model=CustomerNeedRead, status_code=201)
def create_need(payload: CustomerNeedCreate, session: SessionDependency) -> CustomerNeed:
    return CustomerNeedService(session).create_need(payload)


@router.get("/customer-needs", response_model=list[CustomerNeedRead])
def list_needs(organization_id: UUID, session: SessionDependency) -> list[CustomerNeed]:
    return _list(session, CustomerNeed, organization_id)


@router.patch("/customer-needs/{need_id}", response_model=CustomerNeedRead)
def transition_need(
    need_id: UUID, organization_id: UUID, payload: CustomerNeedUpdate, session: SessionDependency
) -> CustomerNeed:
    return CustomerNeedService(session).transition_need(
        scoped_need(session, CustomerNeed, need_id, organization_id), payload.status
    )


@router.post("/pain-need-mappings", response_model=PainNeedMappingRead, status_code=201)
def create_mapping(payload: PainNeedMappingCreate, session: SessionDependency) -> PainNeedMapping:
    return CustomerNeedService(session).map_pain(payload)


@router.get("/pain-need-mappings", response_model=list[PainNeedMappingRead])
def list_mappings(organization_id: UUID, session: SessionDependency) -> list[PainNeedMapping]:
    return _list(session, PainNeedMapping, organization_id)


@router.post("/product-solution-hypotheses", response_model=ProductSolutionRead, status_code=201)
def create_solution(
    payload: ProductSolutionCreate, session: SessionDependency
) -> ProductSolutionHypothesis:
    return CustomerNeedService(session).create_solution(payload)


@router.get("/product-solution-hypotheses", response_model=list[ProductSolutionRead])
def list_solutions(
    organization_id: UUID, session: SessionDependency
) -> list[ProductSolutionHypothesis]:
    return _list(session, ProductSolutionHypothesis, organization_id)


@router.post(
    "/customer-backed-assessments", response_model=CustomerBackedAssessmentRead, status_code=201
)
def create_assessment(
    payload: CustomerBackedAssessmentCreate, session: SessionDependency
) -> CustomerBackedOpportunityAssessment:
    return CustomerNeedService(session).assess(payload)


@router.get("/customer-backed-assessments", response_model=list[CustomerBackedAssessmentRead])
def list_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerBackedOpportunityAssessment]:
    return _list(session, CustomerBackedOpportunityAssessment, organization_id)
