from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.live_revenue_models import (
    CustomerDeliveryItem,
    CustomerServiceDelivery,
    DailyRevenueRun,
    DailyRevenueRunProspect,
    FounderActionItem,
    GrowthExternalDataConnector,
)
from commerce_os.growth.live_revenue_schemas import (
    CustomerDeliveryCreate,
    CustomerDeliveryRead,
    CustomerDeliveryTransition,
    DailyRevenueRunCreate,
    DailyRevenueRunRead,
    DailyRevenueRunTransition,
    DailyRunProspectAdd,
    DailyRunProspectRead,
    DeliveryItemCreate,
    DeliveryItemRead,
    DeliveryItemTransition,
    FounderActionCreate,
    FounderActionDecision,
    FounderActionRead,
    GrowthConnectorCreate,
    GrowthConnectorRead,
    GrowthConnectorTransition,
    LiveRevenueExperimentAnalytics,
)
from commerce_os.growth.live_revenue_services import LiveRevenueService, scoped_live
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


@router.post("/daily-revenue-runs", response_model=DailyRevenueRunRead, status_code=201)
def create_daily_run(
    payload: DailyRevenueRunCreate, request: Request, session: SessionDependency
) -> DailyRevenueRun:
    return LiveRevenueService(session).create_run(payload, actor_id(request))


@router.get("/daily-revenue-runs", response_model=list[DailyRevenueRunRead])
def list_daily_runs(organization_id: UUID, session: SessionDependency) -> list[DailyRevenueRun]:
    return _list(session, DailyRevenueRun, organization_id)


@router.post(
    "/daily-revenue-runs/{run_id}/prospects",
    response_model=DailyRunProspectRead,
    status_code=201,
)
def add_daily_run_prospect(
    run_id: UUID,
    payload: DailyRunProspectAdd,
    request: Request,
    session: SessionDependency,
) -> DailyRevenueRunProspect:
    run = scoped_live(session, DailyRevenueRun, run_id, payload.organization_id)
    return LiveRevenueService(session).add_run_prospect(run, payload, actor_id(request))


@router.patch("/daily-revenue-runs/{run_id}", response_model=DailyRevenueRunRead)
def transition_daily_run(
    run_id: UUID,
    organization_id: UUID,
    payload: DailyRevenueRunTransition,
    request: Request,
    session: SessionDependency,
) -> DailyRevenueRun:
    run = scoped_live(session, DailyRevenueRun, run_id, organization_id)
    return LiveRevenueService(session).transition_run(run, payload.review_status, actor_id(request))


@router.post("/founder-action-items", response_model=FounderActionRead, status_code=201)
def create_founder_action(
    payload: FounderActionCreate, request: Request, session: SessionDependency
) -> FounderActionItem:
    return LiveRevenueService(session).create_action(payload, actor_id(request))


@router.get("/founder-action-items", response_model=list[FounderActionRead])
def list_founder_actions(
    organization_id: UUID, session: SessionDependency
) -> list[FounderActionItem]:
    return _list(session, FounderActionItem, organization_id)


@router.patch("/founder-action-items/{item_id}", response_model=FounderActionRead)
def decide_founder_action(
    item_id: UUID,
    organization_id: UUID,
    payload: FounderActionDecision,
    request: Request,
    session: SessionDependency,
) -> FounderActionItem:
    item = scoped_live(session, FounderActionItem, item_id, organization_id)
    return LiveRevenueService(session).decide_action(
        item, payload.action, payload.assigned_to, payload.notes, actor_id(request)
    )


@router.post("/growth-external-connectors", response_model=GrowthConnectorRead, status_code=201)
def create_growth_connector(
    payload: GrowthConnectorCreate, request: Request, session: SessionDependency
) -> GrowthExternalDataConnector:
    return LiveRevenueService(session).create_connector(payload, actor_id(request))


@router.get("/growth-external-connectors", response_model=list[GrowthConnectorRead])
def list_growth_connectors(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthExternalDataConnector]:
    return _list(session, GrowthExternalDataConnector, organization_id)


@router.patch("/growth-external-connectors/{connector_id}", response_model=GrowthConnectorRead)
def transition_growth_connector(
    connector_id: UUID,
    organization_id: UUID,
    payload: GrowthConnectorTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthExternalDataConnector:
    connector = scoped_live(session, GrowthExternalDataConnector, connector_id, organization_id)
    return LiveRevenueService(session).transition_connector(
        connector, payload.status, actor_id(request)
    )


@router.post("/customer-service-deliveries", response_model=CustomerDeliveryRead, status_code=201)
def create_customer_delivery(
    payload: CustomerDeliveryCreate, request: Request, session: SessionDependency
) -> CustomerServiceDelivery:
    return LiveRevenueService(session).create_delivery(payload, actor_id(request))


@router.get("/customer-service-deliveries", response_model=list[CustomerDeliveryRead])
def list_customer_deliveries(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerServiceDelivery]:
    return _list(session, CustomerServiceDelivery, organization_id)


@router.patch("/customer-service-deliveries/{delivery_id}", response_model=CustomerDeliveryRead)
def transition_customer_delivery(
    delivery_id: UUID,
    organization_id: UUID,
    payload: CustomerDeliveryTransition,
    request: Request,
    session: SessionDependency,
) -> CustomerServiceDelivery:
    delivery = scoped_live(session, CustomerServiceDelivery, delivery_id, organization_id)
    return LiveRevenueService(session).transition_delivery(
        delivery, payload.status, payload.customer_feedback_reference, actor_id(request)
    )


@router.post(
    "/customer-service-deliveries/{delivery_id}/items",
    response_model=DeliveryItemRead,
    status_code=201,
)
def create_delivery_item(
    delivery_id: UUID,
    payload: DeliveryItemCreate,
    request: Request,
    session: SessionDependency,
) -> CustomerDeliveryItem:
    delivery = scoped_live(session, CustomerServiceDelivery, delivery_id, payload.organization_id)
    return LiveRevenueService(session).create_delivery_item(delivery, payload, actor_id(request))


@router.patch("/customer-delivery-items/{item_id}", response_model=DeliveryItemRead)
def transition_delivery_item(
    item_id: UUID,
    organization_id: UUID,
    payload: DeliveryItemTransition,
    request: Request,
    session: SessionDependency,
) -> CustomerDeliveryItem:
    item = scoped_live(session, CustomerDeliveryItem, item_id, organization_id)
    return LiveRevenueService(session).transition_delivery_item(
        item, payload.status, payload.evidence_reference, actor_id(request)
    )


@router.get(
    "/revenue-experiments/{experiment_id}/live-analytics",
    response_model=LiveRevenueExperimentAnalytics,
)
def live_revenue_analytics(
    experiment_id: UUID, organization_id: UUID, session: SessionDependency
) -> LiveRevenueExperimentAnalytics:
    return LiveRevenueService(session).analytics(experiment_id, organization_id)
