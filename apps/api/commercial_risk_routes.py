from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.commercial_risk_models import (
    CommercialViabilityAssessment,
    ProductRiskAssessment,
    ProductRiskSignal,
)
from commerce_os.intelligence.commercial_risk_schemas import (
    CommercialViabilityCreate,
    CommercialViabilityRead,
    ProductRiskAssessmentCreate,
    ProductRiskAssessmentRead,
    ProductRiskSignalCreate,
    ProductRiskSignalRead,
    ProductRiskSignalUpdate,
)
from commerce_os.intelligence.commercial_risk_services import CommercialRiskService
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


@router.post("/product-risk-signals", response_model=ProductRiskSignalRead, status_code=201)
def create_signal(
    payload: ProductRiskSignalCreate, session: SessionDependency
) -> ProductRiskSignal:
    return CommercialRiskService(session).create_signal(payload)


@router.get("/product-risk-signals", response_model=list[ProductRiskSignalRead])
def list_signals(organization_id: UUID, session: SessionDependency) -> list[ProductRiskSignal]:
    return _list(session, ProductRiskSignal, organization_id)


@router.patch("/product-risk-signals/{signal_id}", response_model=ProductRiskSignalRead)
def transition_signal(
    signal_id: UUID,
    organization_id: UUID,
    payload: ProductRiskSignalUpdate,
    session: SessionDependency,
) -> ProductRiskSignal:
    service = CommercialRiskService(session)
    return service.transition_signal(
        service.scoped_signal(signal_id, organization_id), payload.status
    )


@router.post("/product-risk-assessments", response_model=ProductRiskAssessmentRead, status_code=201)
def create_risk_assessment(
    payload: ProductRiskAssessmentCreate, session: SessionDependency
) -> ProductRiskAssessment:
    return CommercialRiskService(session).assess_risk(payload)


@router.get("/product-risk-assessments", response_model=list[ProductRiskAssessmentRead])
def list_risk_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[ProductRiskAssessment]:
    return _list(session, ProductRiskAssessment, organization_id)


@router.post(
    "/commercial-viability-assessments",
    response_model=CommercialViabilityRead,
    status_code=201,
)
def create_viability_assessment(
    payload: CommercialViabilityCreate, session: SessionDependency
) -> CommercialViabilityAssessment:
    return CommercialRiskService(session).assess_viability(payload)


@router.get("/commercial-viability-assessments", response_model=list[CommercialViabilityRead])
def list_viability_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[CommercialViabilityAssessment]:
    return _list(session, CommercialViabilityAssessment, organization_id)
