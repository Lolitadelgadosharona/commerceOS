from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.revenue_conversation_models import (
    CustomerIntentJourney,
    SalesIntentSignal,
    SupportLearningSignal,
)
from commerce_os.intelligence.revenue_conversation_schemas import (
    IntentJourneyCreate,
    IntentJourneyRead,
    IntentJourneyTransition,
    JourneyDashboardRead,
    SalesIntentCreate,
    SalesIntentRead,
    SupportLearningCreate,
    SupportLearningRead,
)
from commerce_os.intelligence.revenue_conversation_services import RevenueConversationService
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


@router.post("/customer-intent-journeys", response_model=IntentJourneyRead, status_code=201)
def create_journey(
    payload: IntentJourneyCreate, request: Request, session: SessionDependency
) -> CustomerIntentJourney:
    return RevenueConversationService(session).create_journey(payload, actor_id(request))


@router.get("/customer-intent-journeys", response_model=list[IntentJourneyRead])
def list_journeys(organization_id: UUID, session: SessionDependency) -> list[CustomerIntentJourney]:
    return _list(session, CustomerIntentJourney, organization_id)


@router.patch("/customer-intent-journeys/{entity_id}", response_model=IntentJourneyRead)
def transition_journey(
    entity_id: UUID,
    organization_id: UUID,
    payload: IntentJourneyTransition,
    request: Request,
    session: SessionDependency,
) -> CustomerIntentJourney:
    service = RevenueConversationService(session)
    entity = service.scoped(CustomerIntentJourney, entity_id, organization_id)
    return service.transition_journey(entity, payload, actor_id(request))


@router.post("/sales-intent-signals", response_model=SalesIntentRead, status_code=201)
def create_sales_signal(
    payload: SalesIntentCreate, request: Request, session: SessionDependency
) -> SalesIntentSignal:
    return RevenueConversationService(session).create_sales_signal(payload, actor_id(request))


@router.get("/sales-intent-signals", response_model=list[SalesIntentRead])
def list_sales_signals(
    organization_id: UUID, session: SessionDependency
) -> list[SalesIntentSignal]:
    return _list(session, SalesIntentSignal, organization_id)


@router.post("/support-learning-signals", response_model=SupportLearningRead, status_code=201)
def create_support_learning(
    payload: SupportLearningCreate, request: Request, session: SessionDependency
) -> SupportLearningSignal:
    return RevenueConversationService(session).create_support_learning(payload, actor_id(request))


@router.get("/support-learning-signals", response_model=list[SupportLearningRead])
def list_support_learning(
    organization_id: UUID, session: SessionDependency
) -> list[SupportLearningSignal]:
    return _list(session, SupportLearningSignal, organization_id)


@router.get("/revenue-conversation-dashboard", response_model=JourneyDashboardRead)
def dashboard(organization_id: UUID, session: SessionDependency) -> JourneyDashboardRead:
    return RevenueConversationService(session).dashboard(organization_id)
