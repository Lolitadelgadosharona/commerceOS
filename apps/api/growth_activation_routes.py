from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.activation_models import (
    OutreachTrackingEvent,
    ProspectExperimentLink,
    RevenueExperiment,
)
from commerce_os.growth.activation_schemas import (
    OutreachEventCreate,
    OutreachEventRead,
    ProspectAssignmentCreate,
    ProspectAssignmentRead,
    ProspectPromotionCreate,
    RevenueExperimentCreate,
    RevenueExperimentRead,
    RevenueExperimentTransition,
)
from commerce_os.growth.activation_services import (
    RevenueActivationService,
    scoped_activation,
)
from commerce_os.growth.discovery_models import ProspectCandidate
from commerce_os.growth.discovery_services import scoped_growth_discovery
from commerce_os.growth.revenue_models import GrowthProspect
from commerce_os.growth.revenue_schemas import ProspectRead
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


@router.post(
    "/prospect-candidates/{candidate_id}/activate",
    response_model=ProspectRead,
    status_code=201,
)
def activate_candidate(
    candidate_id: UUID,
    payload: ProspectPromotionCreate,
    request: Request,
    session: SessionDependency,
) -> GrowthProspect:
    candidate = scoped_growth_discovery(
        session, ProspectCandidate, candidate_id, payload.organization_id
    )
    return RevenueActivationService(session).promote_candidate(
        candidate, payload, actor_id(request)
    )


@router.post("/revenue-experiments", response_model=RevenueExperimentRead, status_code=201)
def create_experiment(
    payload: RevenueExperimentCreate, request: Request, session: SessionDependency
) -> RevenueExperiment:
    return RevenueActivationService(session).create_experiment(payload, actor_id(request))


@router.get("/revenue-experiments", response_model=list[RevenueExperimentRead])
def list_experiments(organization_id: UUID, session: SessionDependency) -> list[RevenueExperiment]:
    return _list(session, RevenueExperiment, organization_id)


@router.patch("/revenue-experiments/{experiment_id}", response_model=RevenueExperimentRead)
def transition_experiment(
    experiment_id: UUID,
    organization_id: UUID,
    payload: RevenueExperimentTransition,
    request: Request,
    session: SessionDependency,
) -> RevenueExperiment:
    experiment = scoped_activation(session, RevenueExperiment, experiment_id, organization_id)
    return RevenueActivationService(session).transition_experiment(
        experiment, payload.status, actor_id(request)
    )


@router.post("/prospect-experiment-links", response_model=ProspectAssignmentRead, status_code=201)
def assign_prospect(
    payload: ProspectAssignmentCreate, request: Request, session: SessionDependency
) -> ProspectExperimentLink:
    return RevenueActivationService(session).assign_prospect(payload, actor_id(request))


@router.get("/prospect-experiment-links", response_model=list[ProspectAssignmentRead])
def list_assignments(
    organization_id: UUID, session: SessionDependency
) -> list[ProspectExperimentLink]:
    return _list(session, ProspectExperimentLink, organization_id)


@router.post("/outreach-tracking-events", response_model=OutreachEventRead, status_code=201)
def record_event(
    payload: OutreachEventCreate, request: Request, session: SessionDependency
) -> OutreachTrackingEvent:
    return RevenueActivationService(session).record_event(payload, actor_id(request))


@router.get("/outreach-tracking-events", response_model=list[OutreachEventRead])
def list_events(organization_id: UUID, session: SessionDependency) -> list[OutreachTrackingEvent]:
    return _list(session, OutreachTrackingEvent, organization_id)
