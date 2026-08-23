from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.revenue_operations_models import (
    DailyExperimentWorkspaceItem,
    EmailWorkflowReference,
    GrowthCustomerFeedback,
)
from commerce_os.growth.revenue_operations_schemas import (
    CustomerFeedbackCreate,
    CustomerFeedbackDecision,
    CustomerFeedbackRead,
    EmailWorkflowReferenceCreate,
    EmailWorkflowReferenceRead,
    RevenueExperimentOperationsDashboard,
    WorkspaceDecision,
    WorkspaceItemCreate,
    WorkspaceItemRead,
)
from commerce_os.growth.revenue_operations_services import (
    RevenueOperationsService,
    scoped_operations,
)
from commerce_os.learning.schemas import LearningObservationCreate
from commerce_os.learning.services import ClosedLoopLearningService
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


@router.post("/daily-experiment-workspace", response_model=WorkspaceItemRead, status_code=201)
def create_workspace_item(
    payload: WorkspaceItemCreate, request: Request, session: SessionDependency
) -> DailyExperimentWorkspaceItem:
    return RevenueOperationsService(session).create_workspace_item(payload, actor_id(request))


@router.get("/daily-experiment-workspace", response_model=list[WorkspaceItemRead])
def list_workspace_items(
    organization_id: UUID, session: SessionDependency
) -> list[DailyExperimentWorkspaceItem]:
    return _list(session, DailyExperimentWorkspaceItem, organization_id)


@router.patch("/daily-experiment-workspace/{entity_id}", response_model=WorkspaceItemRead)
def decide_workspace_item(
    entity_id: UUID,
    organization_id: UUID,
    payload: WorkspaceDecision,
    request: Request,
    session: SessionDependency,
) -> DailyExperimentWorkspaceItem:
    entity = scoped_operations(session, DailyExperimentWorkspaceItem, entity_id, organization_id)
    return RevenueOperationsService(session).decide_workspace_item(
        entity, payload.action, payload.review_notes, actor_id(request)
    )


@router.post(
    "/email-workflow-references", response_model=EmailWorkflowReferenceRead, status_code=201
)
def create_email_reference(
    payload: EmailWorkflowReferenceCreate, request: Request, session: SessionDependency
) -> EmailWorkflowReference:
    return RevenueOperationsService(session).create_email_reference(payload, actor_id(request))


@router.get("/email-workflow-references", response_model=list[EmailWorkflowReferenceRead])
def list_email_references(
    organization_id: UUID, session: SessionDependency
) -> list[EmailWorkflowReference]:
    return _list(session, EmailWorkflowReference, organization_id)


@router.post("/growth-customer-feedback", response_model=CustomerFeedbackRead, status_code=201)
def create_customer_feedback(
    payload: CustomerFeedbackCreate, request: Request, session: SessionDependency
) -> GrowthCustomerFeedback:
    return RevenueOperationsService(session).create_feedback(payload, actor_id(request))


@router.get("/growth-customer-feedback", response_model=list[CustomerFeedbackRead])
def list_customer_feedback(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthCustomerFeedback]:
    return _list(session, GrowthCustomerFeedback, organization_id)


@router.patch("/growth-customer-feedback/{entity_id}", response_model=CustomerFeedbackRead)
def decide_customer_feedback(
    entity_id: UUID,
    organization_id: UUID,
    payload: CustomerFeedbackDecision,
    request: Request,
    session: SessionDependency,
) -> GrowthCustomerFeedback:
    entity = scoped_operations(session, GrowthCustomerFeedback, entity_id, organization_id)
    service = RevenueOperationsService(session)
    service.validate_feedback_decision(entity, payload.status)
    observation_id = None
    if payload.status == "approved":
        observation = ClosedLoopLearningService(session).create_observation(
            LearningObservationCreate(
                organization_id=entity.organization_id,
                source_type="growth_customer_feedback",
                source_record_id=entity.id,
                observation_type="approved_customer_feedback",
                observed_at=entity.updated_at,
                evidence_reference=f"growth_customer_feedback:{entity.id}",
                confidence=entity.confidence,
                metadata={
                    "interest_level": entity.interest_level,
                    "objection_category": entity.objection_category,
                    "learning_signal": entity.learning_signal,
                },
            ),
            actor_id(request),
        )
        observation_id = observation.id
    return service.decide_feedback(entity, payload.status, actor_id(request), observation_id)


@router.get(
    "/revenue-experiments/{experiment_id}/operations-dashboard",
    response_model=RevenueExperimentOperationsDashboard,
)
def operations_dashboard(
    experiment_id: UUID, organization_id: UUID, session: SessionDependency
) -> RevenueExperimentOperationsDashboard:
    return RevenueOperationsService(session).dashboard(experiment_id, organization_id)
