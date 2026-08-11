from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.channel_execution_models import (
    ChannelExecutionPlan,
    ChannelPerformanceObservation,
    CreativeChannelExperiment,
    DistributionRecord,
)
from commerce_os.growth.channel_execution_schemas import (
    DistributionCreate,
    DistributionRead,
    DistributionUpdate,
    ExperimentCreate,
    ExperimentRead,
    ExperimentUpdate,
    PerformanceCreate,
    PerformanceRead,
    PlanCreate,
    PlanRead,
    PlanUpdate,
)
from commerce_os.growth.channel_execution_services import ChannelExecutionService
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


@router.post("/channel-execution-plans", response_model=PlanRead, status_code=201)
def create_plan(payload: PlanCreate, session: SessionDependency) -> ChannelExecutionPlan:
    return ChannelExecutionService(session).create_plan(payload)


@router.get("/channel-execution-plans", response_model=list[PlanRead])
def list_plans(organization_id: UUID, session: SessionDependency) -> list[ChannelExecutionPlan]:
    return _list(session, ChannelExecutionPlan, organization_id)


@router.get("/channel-execution-plans/{entity_id}", response_model=PlanRead)
def read_plan(
    entity_id: UUID, organization_id: UUID, session: SessionDependency
) -> ChannelExecutionPlan:
    return ChannelExecutionService(session).scoped(ChannelExecutionPlan, entity_id, organization_id)


@router.patch("/channel-execution-plans/{entity_id}", response_model=PlanRead)
def update_plan(
    entity_id: UUID, payload: PlanUpdate, session: SessionDependency
) -> ChannelExecutionPlan:
    service = ChannelExecutionService(session)
    return service.update_plan(
        service.scoped(ChannelExecutionPlan, entity_id, payload.organization_id), payload
    )


@router.post("/channel-experiments", response_model=ExperimentRead, status_code=201)
def create_experiment(
    payload: ExperimentCreate, session: SessionDependency
) -> CreativeChannelExperiment:
    return ChannelExecutionService(session).create_experiment(payload)


@router.get("/channel-experiments", response_model=list[ExperimentRead])
def list_experiments(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeChannelExperiment]:
    return _list(session, CreativeChannelExperiment, organization_id)


@router.get("/channel-experiments/{entity_id}", response_model=ExperimentRead)
def read_experiment(
    entity_id: UUID, organization_id: UUID, session: SessionDependency
) -> CreativeChannelExperiment:
    return ChannelExecutionService(session).scoped(
        CreativeChannelExperiment, entity_id, organization_id
    )


@router.patch("/channel-experiments/{entity_id}", response_model=ExperimentRead)
def update_experiment(
    entity_id: UUID, payload: ExperimentUpdate, session: SessionDependency
) -> CreativeChannelExperiment:
    service = ChannelExecutionService(session)
    return service.update_experiment(
        service.scoped(CreativeChannelExperiment, entity_id, payload.organization_id), payload
    )


@router.post("/distribution-records", response_model=DistributionRead, status_code=201)
def create_distribution(
    payload: DistributionCreate, session: SessionDependency
) -> DistributionRecord:
    return ChannelExecutionService(session).create_distribution(payload)


@router.get("/distribution-records", response_model=list[DistributionRead])
def list_distributions(
    organization_id: UUID, session: SessionDependency
) -> list[DistributionRecord]:
    return _list(session, DistributionRecord, organization_id)


@router.get("/distribution-records/{entity_id}", response_model=DistributionRead)
def read_distribution(
    entity_id: UUID, organization_id: UUID, session: SessionDependency
) -> DistributionRecord:
    return ChannelExecutionService(session).scoped(DistributionRecord, entity_id, organization_id)


@router.patch("/distribution-records/{entity_id}", response_model=DistributionRead)
def update_distribution(
    entity_id: UUID, payload: DistributionUpdate, session: SessionDependency
) -> DistributionRecord:
    service = ChannelExecutionService(session)
    return service.update_distribution(
        service.scoped(DistributionRecord, entity_id, payload.organization_id), payload
    )


@router.post("/channel-performance", response_model=PerformanceRead, status_code=201)
def create_performance(
    payload: PerformanceCreate, session: SessionDependency
) -> ChannelPerformanceObservation:
    return ChannelExecutionService(session).create_performance(payload)


@router.get("/channel-performance", response_model=list[PerformanceRead])
def list_performance(
    organization_id: UUID, session: SessionDependency
) -> list[ChannelPerformanceObservation]:
    return _list(session, ChannelPerformanceObservation, organization_id)


@router.get("/channel-performance/{entity_id}", response_model=PerformanceRead)
def read_performance(
    entity_id: UUID, organization_id: UUID, session: SessionDependency
) -> ChannelPerformanceObservation:
    return ChannelExecutionService(session).scoped(
        ChannelPerformanceObservation, entity_id, organization_id
    )
