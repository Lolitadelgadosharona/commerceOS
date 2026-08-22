from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.conversation_learning_models import (
    GrowthMessagePerformanceObservation,
    GrowthObjectionRecord,
    GrowthSalesLearningSignal,
)
from commerce_os.growth.conversation_learning_schemas import (
    ConversationAnalysisTransition,
    MessagePerformanceCreate,
    MessagePerformanceRead,
    ObjectionRecordCreate,
    ObjectionRecordRead,
    SalesKnowledgeDashboardRead,
    SalesLearningSignalCreate,
    SalesLearningSignalRead,
)
from commerce_os.growth.conversation_learning_services import (
    GrowthConversationLearningService,
)
from commerce_os.growth.revenue_models import SalesConversationAnalysis
from commerce_os.growth.revenue_schemas import SalesAnalysisRead
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.growth_learning_orchestration import create_growth_sales_learning_signal
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


@router.patch("/sales-conversation-analyses/{analysis_id}", response_model=SalesAnalysisRead)
def transition_analysis(
    analysis_id: UUID,
    organization_id: UUID,
    payload: ConversationAnalysisTransition,
    request: Request,
    session: SessionDependency,
) -> SalesConversationAnalysis:
    analysis = scoped_revenue(session, SalesConversationAnalysis, analysis_id, organization_id)
    return GrowthConversationLearningService(session).transition_analysis(
        analysis, payload.status, actor_id(request)
    )


@router.post("/growth-objections", response_model=ObjectionRecordRead, status_code=201)
def create_objection(
    payload: ObjectionRecordCreate, request: Request, session: SessionDependency
) -> GrowthObjectionRecord:
    return GrowthConversationLearningService(session).create_objection(payload, actor_id(request))


@router.get("/growth-objections", response_model=list[ObjectionRecordRead])
def list_objections(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthObjectionRecord]:
    return _list(session, GrowthObjectionRecord, organization_id)


@router.post(
    "/growth-sales-learning-signals",
    response_model=SalesLearningSignalRead,
    status_code=201,
)
def create_learning_signal(
    payload: SalesLearningSignalCreate, request: Request, session: SessionDependency
) -> GrowthSalesLearningSignal:
    return create_growth_sales_learning_signal(session, payload, actor_id(request))


@router.get("/growth-sales-learning-signals", response_model=list[SalesLearningSignalRead])
def list_learning_signals(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthSalesLearningSignal]:
    return _list(session, GrowthSalesLearningSignal, organization_id)


@router.post(
    "/growth-message-performance",
    response_model=MessagePerformanceRead,
    status_code=201,
)
def create_message_performance(
    payload: MessagePerformanceCreate, request: Request, session: SessionDependency
) -> GrowthMessagePerformanceObservation:
    return GrowthConversationLearningService(session).create_message_performance(
        payload, actor_id(request)
    )


@router.get("/growth-message-performance", response_model=list[MessagePerformanceRead])
def list_message_performance(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthMessagePerformanceObservation]:
    return _list(session, GrowthMessagePerformanceObservation, organization_id)


@router.get("/growth-sales-knowledge-dashboard", response_model=SalesKnowledgeDashboardRead)
def sales_knowledge_dashboard(
    organization_id: UUID, session: SessionDependency
) -> SalesKnowledgeDashboardRead:
    return GrowthConversationLearningService(session).dashboard(organization_id)
