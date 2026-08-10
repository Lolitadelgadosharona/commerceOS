from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.decision.creative_models import (
    CreativeBrief,
    CreativeChannelFit,
    CreativeExperiment,
    CreativeHypothesis,
    CreativeStrategy,
    CreativeStrategyStatus,
)
from commerce_os.decision.creative_schemas import (
    CreativeBriefCreate,
    CreativeBriefRead,
    CreativeChannelFitCreate,
    CreativeChannelFitRead,
    CreativeExperimentCreate,
    CreativeExperimentRead,
    CreativeExperimentUpdate,
    CreativeHypothesisCreate,
    CreativeHypothesisRead,
    CreativeStrategyCreate,
    CreativeStrategyRead,
    CreativeStrategyUpdate,
)
from commerce_os.decision.creative_services import (
    CreativePlanningService,
    CreativeStrategyService,
    scoped_strategy,
)
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post(
    "/creative-strategies",
    response_model=CreativeStrategyRead,
    status_code=201,
    tags=["creative_strategies"],
)
def create_strategy(
    payload: CreativeStrategyCreate, session: SessionDependency
) -> CreativeStrategy:
    return CreativeStrategyService(session).create(payload)


@router.get(
    "/creative-strategies", response_model=list[CreativeStrategyRead], tags=["creative_strategies"]
)
def list_strategies(organization_id: UUID, session: SessionDependency) -> list[CreativeStrategy]:
    return _list(session, CreativeStrategy, organization_id)


@router.patch(
    "/creative-strategies/{strategy_id}",
    response_model=CreativeStrategyRead,
    tags=["creative_strategies"],
)
def transition_strategy(
    strategy_id: UUID,
    organization_id: UUID,
    payload: CreativeStrategyUpdate,
    session: SessionDependency,
) -> CreativeStrategy:
    return CreativeStrategyService(session).transition(
        scoped_strategy(session, strategy_id, organization_id),
        CreativeStrategyStatus(payload.status),
    )


@router.post(
    "/creative-hypotheses",
    response_model=CreativeHypothesisRead,
    status_code=201,
    tags=["creative_hypotheses"],
)
def create_hypothesis(
    payload: CreativeHypothesisCreate, session: SessionDependency
) -> CreativeHypothesis:
    return CreativePlanningService(session).create_hypothesis(payload)


@router.get(
    "/creative-hypotheses",
    response_model=list[CreativeHypothesisRead],
    tags=["creative_hypotheses"],
)
def list_hypotheses(organization_id: UUID, session: SessionDependency) -> list[CreativeHypothesis]:
    return _list(session, CreativeHypothesis, organization_id)


@router.post(
    "/creative-briefs", response_model=CreativeBriefRead, status_code=201, tags=["creative_briefs"]
)
def create_brief(payload: CreativeBriefCreate, session: SessionDependency) -> CreativeBrief:
    return CreativePlanningService(session).create_brief(payload)


@router.get("/creative-briefs", response_model=list[CreativeBriefRead], tags=["creative_briefs"])
def list_briefs(organization_id: UUID, session: SessionDependency) -> list[CreativeBrief]:
    return _list(session, CreativeBrief, organization_id)


@router.post(
    "/creative-channel-fits",
    response_model=CreativeChannelFitRead,
    status_code=201,
    tags=["creative_channel_fits"],
)
def create_channel_fit(
    payload: CreativeChannelFitCreate, session: SessionDependency
) -> CreativeChannelFit:
    return CreativePlanningService(session).create_channel_fit(payload)


@router.get(
    "/creative-channel-fits",
    response_model=list[CreativeChannelFitRead],
    tags=["creative_channel_fits"],
)
def list_channel_fits(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeChannelFit]:
    return _list(session, CreativeChannelFit, organization_id)


@router.post(
    "/creative-experiments",
    response_model=CreativeExperimentRead,
    status_code=201,
    tags=["creative_experiments"],
)
def create_experiment(
    payload: CreativeExperimentCreate, session: SessionDependency
) -> CreativeExperiment:
    return CreativePlanningService(session).create_experiment(payload)


@router.get(
    "/creative-experiments",
    response_model=list[CreativeExperimentRead],
    tags=["creative_experiments"],
)
def list_experiments(organization_id: UUID, session: SessionDependency) -> list[CreativeExperiment]:
    return _list(session, CreativeExperiment, organization_id)


@router.patch(
    "/creative-experiments/{experiment_id}",
    response_model=CreativeExperimentRead,
    tags=["creative_experiments"],
)
def transition_experiment(
    experiment_id: UUID,
    organization_id: UUID,
    payload: CreativeExperimentUpdate,
    session: SessionDependency,
) -> CreativeExperiment:
    experiment = session.get(CreativeExperiment, experiment_id)
    if experiment is None or experiment.organization_id != organization_id:
        raise DecisionScopeError("Creative experiment was not found in this organization.")
    return CreativePlanningService(session).transition_experiment(experiment, payload)
