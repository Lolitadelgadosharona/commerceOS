from typing import Annotated
from uuid import UUID

from commerce_os.decision.customer_value_models import CustomerValueAssessment
from commerce_os.decision.customer_value_schemas import CustomerValueCreate, CustomerValueRead
from commerce_os.decision.customer_value_services import CustomerValueService
from commerce_os.intelligence.customer_360_models import Customer360Profile, CustomerJourneyEvent
from commerce_os.intelligence.customer_360_schemas import (
    Customer360Read,
    JourneyEventCreate,
    JourneyEventRead,
)
from commerce_os.intelligence.customer_360_services import Customer360Service
from commerce_os.operations.customer_identity_models import CustomerIdentityLink
from commerce_os.operations.customer_identity_schemas import IdentityLinkCreate, IdentityLinkRead
from commerce_os.operations.customer_identity_services import CustomerIdentityLinkService
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/customer-identity-links", response_model=IdentityLinkRead, status_code=201)
def create_identity(
    payload: IdentityLinkCreate, session: SessionDependency
) -> CustomerIdentityLink:
    return CustomerIdentityLinkService(session).create(payload)


@router.get("/customer-identity-links", response_model=list[IdentityLinkRead])
def list_identities(
    organization_id: UUID, session: SessionDependency, customer_id: UUID | None = None
) -> list[CustomerIdentityLink]:
    statement = select(CustomerIdentityLink).where(
        CustomerIdentityLink.organization_id == organization_id
    )
    if customer_id is not None:
        statement = statement.where(CustomerIdentityLink.customer_id == customer_id)
    return list(session.scalars(statement.order_by(CustomerIdentityLink.created_at.desc())))


@router.post("/customer-journey-events", response_model=JourneyEventRead, status_code=201)
def create_event(payload: JourneyEventCreate, session: SessionDependency) -> CustomerJourneyEvent:
    return Customer360Service(session).create_event(payload)


@router.get("/customer-journey-events", response_model=list[JourneyEventRead])
def list_events(
    organization_id: UUID, session: SessionDependency, customer_id: UUID | None = None
) -> list[CustomerJourneyEvent]:
    statement = select(CustomerJourneyEvent).where(
        CustomerJourneyEvent.organization_id == organization_id
    )
    if customer_id is not None:
        statement = statement.where(CustomerJourneyEvent.customer_id == customer_id)
    return list(session.scalars(statement.order_by(CustomerJourneyEvent.occurred_at.desc())))


@router.get("/customer-360/{customer_id}", response_model=Customer360Read)
def customer_360(
    customer_id: UUID, organization_id: UUID, session: SessionDependency
) -> Customer360Profile:
    return Customer360Service(session).project(customer_id, organization_id)


@router.get("/customer-360", response_model=list[Customer360Read])
def list_customer_360(
    organization_id: UUID, session: SessionDependency
) -> list[Customer360Profile]:
    statement = select(Customer360Profile).where(
        Customer360Profile.organization_id == organization_id
    )
    return list(session.scalars(statement.order_by(Customer360Profile.updated_at.desc())))


@router.post("/customer-value-assessments", response_model=CustomerValueRead, status_code=201)
def create_value(
    payload: CustomerValueCreate, session: SessionDependency
) -> CustomerValueAssessment:
    return CustomerValueService(session).create(payload)


@router.get("/customer-value-assessments", response_model=list[CustomerValueRead])
def list_values(
    organization_id: UUID, session: SessionDependency, customer_id: UUID | None = None
) -> list[CustomerValueAssessment]:
    statement = select(CustomerValueAssessment).where(
        CustomerValueAssessment.organization_id == organization_id
    )
    if customer_id is not None:
        statement = statement.where(CustomerValueAssessment.customer_id == customer_id)
    return list(session.scalars(statement.order_by(CustomerValueAssessment.created_at.desc())))
