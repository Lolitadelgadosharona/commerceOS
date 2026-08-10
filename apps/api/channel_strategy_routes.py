from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.decision.channel_models import (
    ChannelCandidate,
    ChannelDecisionEvidence,
    ChannelMeasurementPlan,
    ChannelOpportunityScore,
    ChannelStrategy,
    ChannelStrategyStatus,
    ConversionPath,
    ConversionPathStep,
)
from commerce_os.decision.channel_schemas import (
    CandidateCreate,
    CandidateRead,
    EvidenceCreate,
    EvidenceRead,
    MeasurementCreate,
    MeasurementRead,
    PathCreate,
    PathRead,
    ScoreCreate,
    ScoreRead,
    StepCreate,
    StepRead,
    StrategyCreate,
    StrategyRead,
    StrategyUpdate,
)
from commerce_os.decision.channel_services import (
    ChannelStrategyService,
    ConversionPathService,
    scoped_path,
    scoped_strategy,
)
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


@router.post("/channel-strategies", response_model=StrategyRead, status_code=201)
def create_strategy(payload: StrategyCreate, session: SessionDependency) -> ChannelStrategy:
    return ChannelStrategyService(session).create(payload)


@router.get("/channel-strategies", response_model=list[StrategyRead])
def list_strategies(organization_id: UUID, session: SessionDependency) -> list[ChannelStrategy]:
    return _list(session, ChannelStrategy, organization_id)


@router.patch("/channel-strategies/{strategy_id}", response_model=StrategyRead)
def transition_strategy(
    strategy_id: UUID,
    organization_id: UUID,
    payload: StrategyUpdate,
    session: SessionDependency,
) -> ChannelStrategy:
    return ChannelStrategyService(session).transition(
        scoped_strategy(session, strategy_id, organization_id),
        ChannelStrategyStatus(payload.status),
    )


@router.post("/channel-candidates", response_model=CandidateRead, status_code=201)
def create_candidate(payload: CandidateCreate, session: SessionDependency) -> ChannelCandidate:
    return ChannelStrategyService(session).create_candidate(payload)


@router.get("/channel-candidates", response_model=list[CandidateRead])
def list_candidates(organization_id: UUID, session: SessionDependency) -> list[ChannelCandidate]:
    return _list(session, ChannelCandidate, organization_id)


@router.post("/channel-opportunity-scores", response_model=ScoreRead, status_code=201)
def score_candidate(payload: ScoreCreate, session: SessionDependency) -> ChannelOpportunityScore:
    return ChannelStrategyService(session).score(payload)


@router.get("/channel-opportunity-scores", response_model=list[ScoreRead])
def list_scores(organization_id: UUID, session: SessionDependency) -> list[ChannelOpportunityScore]:
    return _list(session, ChannelOpportunityScore, organization_id)


@router.post("/conversion-paths", response_model=PathRead, status_code=201)
def create_path(payload: PathCreate, session: SessionDependency) -> ConversionPath:
    return ConversionPathService(session).create(payload)


@router.get("/conversion-paths", response_model=list[PathRead])
def list_paths(organization_id: UUID, session: SessionDependency) -> list[ConversionPath]:
    return _list(session, ConversionPath, organization_id)


@router.post("/conversion-paths/{path_id}/validate", response_model=PathRead)
def validate_path(
    path_id: UUID, organization_id: UUID, session: SessionDependency
) -> ConversionPath:
    return ConversionPathService(session).validate(scoped_path(session, path_id, organization_id))


@router.post("/conversion-path-steps", response_model=StepRead, status_code=201)
def create_step(payload: StepCreate, session: SessionDependency) -> ConversionPathStep:
    return ConversionPathService(session).add_step(payload)


@router.get("/conversion-path-steps", response_model=list[StepRead])
def list_steps(organization_id: UUID, session: SessionDependency) -> list[ConversionPathStep]:
    return _list(session, ConversionPathStep, organization_id)


@router.post("/channel-measurement-plans", response_model=MeasurementRead, status_code=201)
def create_measurement(
    payload: MeasurementCreate, session: SessionDependency
) -> ChannelMeasurementPlan:
    return ChannelStrategyService(session).create_measurement(payload)


@router.get("/channel-measurement-plans", response_model=list[MeasurementRead])
def list_measurements(
    organization_id: UUID, session: SessionDependency
) -> list[ChannelMeasurementPlan]:
    return _list(session, ChannelMeasurementPlan, organization_id)


@router.post("/channel-decision-evidence", response_model=EvidenceRead, status_code=201)
def create_evidence(payload: EvidenceCreate, session: SessionDependency) -> ChannelDecisionEvidence:
    return ChannelStrategyService(session).create_evidence(payload)


@router.get("/channel-decision-evidence", response_model=list[EvidenceRead])
def list_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[ChannelDecisionEvidence]:
    return _list(session, ChannelDecisionEvidence, organization_id)
