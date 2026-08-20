from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.learning.models import (
    ImprovementRecommendation,
    LearningConclusion,
    LearningObservation,
    RecommendationPriorityAssessment,
    RootCauseHypothesis,
)
from commerce_os.learning.schemas import (
    ConclusionCreate,
    ConclusionRead,
    ConclusionTransition,
    FeedbackLoopRead,
    HypothesisCreate,
    HypothesisRead,
    HypothesisTransition,
    LearningDashboardRead,
    LearningObservationCreate,
    LearningObservationRead,
    PriorityCreate,
    PriorityRead,
    RecommendationCreate,
    RecommendationRead,
)
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


@router.post("/learning-observations", response_model=LearningObservationRead, status_code=201)
def create_observation(
    payload: LearningObservationCreate, request: Request, session: SessionDependency
) -> LearningObservation:
    return ClosedLoopLearningService(session).create_observation(payload, actor_id(request))


@router.get("/learning-observations", response_model=list[LearningObservationRead])
def list_observations(
    organization_id: UUID, session: SessionDependency
) -> list[LearningObservation]:
    return _list(session, LearningObservation, organization_id)


@router.post("/root-cause-hypotheses", response_model=HypothesisRead, status_code=201)
def create_hypothesis(
    payload: HypothesisCreate, request: Request, session: SessionDependency
) -> RootCauseHypothesis:
    return ClosedLoopLearningService(session).create_hypothesis(payload, actor_id(request))


@router.get("/root-cause-hypotheses", response_model=list[HypothesisRead])
def list_hypotheses(organization_id: UUID, session: SessionDependency) -> list[RootCauseHypothesis]:
    return _list(session, RootCauseHypothesis, organization_id)


@router.patch("/root-cause-hypotheses/{entity_id}", response_model=HypothesisRead)
def transition_hypothesis(
    entity_id: UUID,
    organization_id: UUID,
    payload: HypothesisTransition,
    request: Request,
    session: SessionDependency,
) -> RootCauseHypothesis:
    service = ClosedLoopLearningService(session)
    return service.transition_hypothesis(
        service.scoped(RootCauseHypothesis, entity_id, organization_id),
        payload.status,
        actor_id(request),
    )


@router.post("/learning-conclusions", response_model=ConclusionRead, status_code=201)
def create_conclusion(
    payload: ConclusionCreate, request: Request, session: SessionDependency
) -> LearningConclusion:
    return ClosedLoopLearningService(session).create_conclusion(payload, actor_id(request))


@router.patch("/learning-conclusions/{entity_id}", response_model=ConclusionRead)
def transition_conclusion(
    entity_id: UUID,
    organization_id: UUID,
    payload: ConclusionTransition,
    request: Request,
    session: SessionDependency,
) -> LearningConclusion:
    service = ClosedLoopLearningService(session)
    return service.transition_conclusion(
        service.scoped(LearningConclusion, entity_id, organization_id), payload, actor_id(request)
    )


@router.post("/improvement-recommendations", response_model=RecommendationRead, status_code=201)
def create_recommendation(
    payload: RecommendationCreate, request: Request, session: SessionDependency
) -> ImprovementRecommendation:
    return ClosedLoopLearningService(session).create_recommendation(payload, actor_id(request))


@router.get("/improvement-recommendations", response_model=list[RecommendationRead])
def list_recommendations(
    organization_id: UUID, session: SessionDependency
) -> list[ImprovementRecommendation]:
    return _list(session, ImprovementRecommendation, organization_id)


@router.post("/recommendation-priorities", response_model=PriorityRead, status_code=201)
def assess_priority(
    payload: PriorityCreate, request: Request, session: SessionDependency
) -> RecommendationPriorityAssessment:
    return ClosedLoopLearningService(session).assess_priority(payload, actor_id(request))


@router.post(
    "/improvement-recommendations/{entity_id}/decision-queue", response_model=RecommendationRead
)
def queue_recommendation(
    entity_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ImprovementRecommendation:
    service = ClosedLoopLearningService(session)
    recommendation = service.scoped(ImprovementRecommendation, entity_id, organization_id)
    _, high_risk = service.review_queue_priority(recommendation)
    queue = DecisionQueueService(session).create(
        DecisionQueueCreate(
            organization_id=recommendation.organization_id,
            title=f"Review improvement: {recommendation.target_type}",
            domain="learning",
            reason=recommendation.rationale,
            priority="critical" if high_risk else "high",
            required_action="review",
        )
    )
    return service.attach_decision_queue(recommendation, queue.id, actor_id(request))


@router.get("/learning-feedback-loops/{recommendation_id}", response_model=FeedbackLoopRead)
def feedback_loop(
    recommendation_id: UUID, organization_id: UUID, session: SessionDependency
) -> FeedbackLoopRead:
    return ClosedLoopLearningService(session).feedback_loop(recommendation_id, organization_id)


@router.get("/learning-dashboard", response_model=LearningDashboardRead)
def dashboard(organization_id: UUID, session: SessionDependency) -> LearningDashboardRead:
    return ClosedLoopLearningService(session).dashboard(organization_id)
