from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.experiment_models import (
    DistributionCampaign,
    ExperimentVariant,
    GrowthCreativeExperiment,
    GrowthLearningSignal,
    GrowthPerformanceObservation,
)
from commerce_os.growth.experiment_schemas import (
    DistributionCampaignCreate,
    DistributionCampaignRead,
    DistributionCampaignTransition,
    ExperimentVariantCreate,
    ExperimentVariantRead,
    GrowthExperimentCreate,
    GrowthExperimentRead,
    GrowthExperimentTransition,
    GrowthLearningSignalCreate,
    GrowthLearningSignalRead,
    GrowthPerformanceCreate,
    GrowthPerformanceRead,
)
from commerce_os.growth.experiment_services import GrowthExperimentService, scoped_growth
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


@router.post("/growth-experiments", response_model=GrowthExperimentRead, status_code=201)
def create_experiment(
    payload: GrowthExperimentCreate, request: Request, session: SessionDependency
) -> GrowthCreativeExperiment:
    return GrowthExperimentService(session).create_experiment(payload, actor_id(request))


@router.get("/growth-experiments", response_model=list[GrowthExperimentRead])
def list_experiments(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthCreativeExperiment]:
    return _list(session, GrowthCreativeExperiment, organization_id)


@router.patch("/growth-experiments/{entity_id}", response_model=GrowthExperimentRead)
def transition_experiment(
    entity_id: UUID,
    organization_id: UUID,
    payload: GrowthExperimentTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthCreativeExperiment:
    entity = scoped_growth(session, GrowthCreativeExperiment, entity_id, organization_id)
    return GrowthExperimentService(session).transition_experiment(
        entity, payload.status, actor_id(request), payload.approval_request_id
    )


@router.post("/growth-experiment-variants", response_model=ExperimentVariantRead, status_code=201)
def create_variant(
    payload: ExperimentVariantCreate, request: Request, session: SessionDependency
) -> ExperimentVariant:
    return GrowthExperimentService(session).create_variant(payload, actor_id(request))


@router.get("/growth-experiment-variants", response_model=list[ExperimentVariantRead])
def list_variants(organization_id: UUID, session: SessionDependency) -> list[ExperimentVariant]:
    return _list(session, ExperimentVariant, organization_id)


@router.post("/distribution-campaigns", response_model=DistributionCampaignRead, status_code=201)
def create_campaign(
    payload: DistributionCampaignCreate, request: Request, session: SessionDependency
) -> DistributionCampaign:
    return GrowthExperimentService(session).create_campaign(payload, actor_id(request))


@router.get("/distribution-campaigns", response_model=list[DistributionCampaignRead])
def list_campaigns(organization_id: UUID, session: SessionDependency) -> list[DistributionCampaign]:
    return _list(session, DistributionCampaign, organization_id)


@router.patch("/distribution-campaigns/{entity_id}", response_model=DistributionCampaignRead)
def transition_campaign(
    entity_id: UUID,
    organization_id: UUID,
    payload: DistributionCampaignTransition,
    request: Request,
    session: SessionDependency,
) -> DistributionCampaign:
    entity = scoped_growth(session, DistributionCampaign, entity_id, organization_id)
    return GrowthExperimentService(session).transition_campaign(
        entity, payload.lifecycle_state, actor_id(request), payload.approval_request_id
    )


@router.post(
    "/growth-performance-observations", response_model=GrowthPerformanceRead, status_code=201
)
def create_performance(
    payload: GrowthPerformanceCreate, request: Request, session: SessionDependency
) -> GrowthPerformanceObservation:
    return GrowthExperimentService(session).create_performance(payload, actor_id(request))


@router.get("/growth-performance-observations", response_model=list[GrowthPerformanceRead])
def list_performance(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthPerformanceObservation]:
    return _list(session, GrowthPerformanceObservation, organization_id)


@router.post("/growth-learning-signals", response_model=GrowthLearningSignalRead, status_code=201)
def create_learning(
    payload: GrowthLearningSignalCreate, request: Request, session: SessionDependency
) -> GrowthLearningSignal:
    return GrowthExperimentService(session).create_learning(payload, actor_id(request))


@router.get("/growth-learning-signals", response_model=list[GrowthLearningSignalRead])
def list_learning(organization_id: UUID, session: SessionDependency) -> list[GrowthLearningSignal]:
    return _list(session, GrowthLearningSignal, organization_id)
