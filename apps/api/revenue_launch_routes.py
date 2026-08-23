from datetime import date
from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.revenue_launch_models import (
    CustomerLifecycleEvent,
    PaymentReadinessRecord,
    ProspectRevenuePipeline,
    RevenueOfferTracking,
)
from commerce_os.growth.revenue_launch_schemas import (
    CustomerLifecycleEventCreate,
    CustomerLifecycleEventRead,
    PaymentReadinessCreate,
    PaymentReadinessRead,
    PaymentStatusTransition,
    RevenueCommandCenter,
    RevenueOfferCreate,
    RevenueOfferRead,
    RevenueOfferTransition,
    RevenuePipelineCreate,
    RevenuePipelineRead,
    RevenuePipelineTransition,
)
from commerce_os.growth.revenue_launch_services import RevenueLaunchService, scoped_launch
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.market_connector_routes import initiating_actor

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def actor_id(request: Request) -> UUID:
    actor = initiating_actor(request)
    if actor is None:
        raise ApiError(401, "actor_required", "Verified actor identity is required.")
    return actor


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/revenue-pipelines", response_model=RevenuePipelineRead, status_code=201)
def create_pipeline(
    payload: RevenuePipelineCreate, request: Request, session: SessionDependency
) -> ProspectRevenuePipeline:
    return RevenueLaunchService(session).create_pipeline(payload, actor_id(request))


@router.get("/revenue-pipelines", response_model=list[RevenuePipelineRead])
def list_pipelines(
    organization_id: UUID, session: SessionDependency
) -> list[ProspectRevenuePipeline]:
    return _list(session, ProspectRevenuePipeline, organization_id)


@router.patch("/revenue-pipelines/{entity_id}", response_model=RevenuePipelineRead)
def transition_pipeline(
    entity_id: UUID,
    organization_id: UUID,
    payload: RevenuePipelineTransition,
    request: Request,
    session: SessionDependency,
) -> ProspectRevenuePipeline:
    entity = scoped_launch(session, ProspectRevenuePipeline, entity_id, organization_id)
    return RevenueLaunchService(session).transition_pipeline(
        entity, payload.stage, payload.notes, actor_id(request)
    )


@router.post("/revenue-offers", response_model=RevenueOfferRead, status_code=201)
def create_offer(
    payload: RevenueOfferCreate, request: Request, session: SessionDependency
) -> RevenueOfferTracking:
    return RevenueLaunchService(session).create_offer(payload, actor_id(request))


@router.get("/revenue-offers", response_model=list[RevenueOfferRead])
def list_offers(organization_id: UUID, session: SessionDependency) -> list[RevenueOfferTracking]:
    return _list(session, RevenueOfferTracking, organization_id)


@router.patch("/revenue-offers/{entity_id}", response_model=RevenueOfferRead)
def transition_offer(
    entity_id: UUID,
    organization_id: UUID,
    payload: RevenueOfferTransition,
    request: Request,
    session: SessionDependency,
) -> RevenueOfferTracking:
    entity = scoped_launch(session, RevenueOfferTracking, entity_id, organization_id)
    return RevenueLaunchService(session).transition_offer(
        entity, payload.status, payload.customer_response, actor_id(request)
    )


@router.post("/payment-readiness", response_model=PaymentReadinessRead, status_code=201)
def create_payment_readiness(
    payload: PaymentReadinessCreate, request: Request, session: SessionDependency
) -> PaymentReadinessRecord:
    return RevenueLaunchService(session).create_payment_readiness(payload, actor_id(request))


@router.get("/payment-readiness", response_model=list[PaymentReadinessRead])
def list_payment_readiness(
    organization_id: UUID, session: SessionDependency
) -> list[PaymentReadinessRecord]:
    return _list(session, PaymentReadinessRecord, organization_id)


@router.patch("/payment-readiness/{entity_id}", response_model=PaymentReadinessRead)
def transition_payment(
    entity_id: UUID,
    organization_id: UUID,
    payload: PaymentStatusTransition,
    request: Request,
    session: SessionDependency,
) -> PaymentReadinessRecord:
    entity = scoped_launch(session, PaymentReadinessRecord, entity_id, organization_id)
    return RevenueLaunchService(session).transition_payment(
        entity, payload.payment_status, payload.revenue_observation_id, actor_id(request)
    )


@router.post(
    "/customer-lifecycle-events", response_model=CustomerLifecycleEventRead, status_code=201
)
def create_lifecycle_event(
    payload: CustomerLifecycleEventCreate, request: Request, session: SessionDependency
) -> CustomerLifecycleEvent:
    return RevenueLaunchService(session).create_lifecycle_event(payload, actor_id(request))


@router.get("/customer-lifecycle-events", response_model=list[CustomerLifecycleEventRead])
def list_lifecycle_events(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerLifecycleEvent]:
    return _list(session, CustomerLifecycleEvent, organization_id)


@router.get("/revenue-command-center", response_model=RevenueCommandCenter)
def revenue_command_center(
    organization_id: UUID, dashboard_date: date, session: SessionDependency
) -> RevenueCommandCenter:
    return RevenueLaunchService(session).command_center(organization_id, dashboard_date)
