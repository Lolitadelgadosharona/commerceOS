from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.decision.creative_models import (
    CreativeBrief,
    CreativeChannelFit,
    CreativeExperiment,
    CreativeExperimentStatus,
    CreativeHypothesis,
    CreativeStrategy,
    CreativeStrategyStatus,
)
from commerce_os.decision.creative_schemas import (
    CreativeBriefCreate,
    CreativeChannelFitCreate,
    CreativeExperimentCreate,
    CreativeExperimentUpdate,
    CreativeHypothesisCreate,
    CreativeStrategyCreate,
)
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
STRATEGY_TRANSITIONS = {
    "draft": {"approved", "archived"},
    "approved": {"active", "archived"},
    "active": {"archived"},
    "archived": set(),
}
EXPERIMENT_TRANSITIONS = {"planned": {"running"}, "running": {"completed"}, "completed": set()}


def scoped_strategy(session: Session, strategy_id: UUID, organization_id: UUID) -> CreativeStrategy:
    strategy = session.get(CreativeStrategy, strategy_id)
    if strategy is None or strategy.organization_id != organization_id:
        raise DecisionScopeError("Creative strategy was not found in this organization.")
    return strategy


def scoped_hypothesis(
    session: Session, hypothesis_id: UUID, organization_id: UUID
) -> CreativeHypothesis:
    hypothesis = session.get(CreativeHypothesis, hypothesis_id)
    if hypothesis is None or hypothesis.organization_id != organization_id:
        raise DecisionScopeError("Creative hypothesis was not found in this organization.")
    return hypothesis


class CreativeStrategyService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CreativeStrategyCreate) -> CreativeStrategy:
        if not reference_belongs_to_organization(
            self.session,
            table_name="products",
            reference_id=payload.product_id,
            organization_id=payload.organization_id,
        ):
            raise DecisionScopeError("Product was not found in this organization.")
        return self._save(
            CreativeStrategy(**payload.model_dump(), status=CreativeStrategyStatus.DRAFT)
        )

    def transition(
        self, strategy: CreativeStrategy, status: CreativeStrategyStatus
    ) -> CreativeStrategy:
        if status.value not in STRATEGY_TRANSITIONS[str(strategy.status)]:
            raise DecisionStateError(
                f"Creative strategy cannot transition from {strategy.status} to {status.value}."
            )
        strategy.status = status
        return self._save(strategy)

    def _save(self, value: CreativeStrategy) -> CreativeStrategy:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value


class CreativePlanningService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_hypothesis(self, payload: CreativeHypothesisCreate) -> CreativeHypothesis:
        scoped_strategy(self.session, payload.strategy_id, payload.organization_id)
        return self._save(CreativeHypothesis(**payload.model_dump()))

    def create_brief(self, payload: CreativeBriefCreate) -> CreativeBrief:
        strategy_id = payload.creative_strategy_id or payload.strategy_id
        if strategy_id is None:  # enforced by the schema; keeps typing explicit
            raise DecisionStateError("Creative strategy is required.")
        strategy = scoped_strategy(self.session, strategy_id, payload.organization_id)
        if payload.product_id is not None and payload.product_id != strategy.product_id:
            raise DecisionScopeError("Creative strategy does not belong to the supplied product.")
        proof_requirements = payload.proof_requirements or payload.proof_points
        cta_strategy = payload.cta_strategy or payload.cta
        if proof_requirements is None or cta_strategy is None:
            raise DecisionStateError("Brief proof and CTA strategy are required.")
        values = payload.model_dump(exclude={"creative_strategy_id", "product_id", "strategy_id"})
        values.update(
            {
                "organization_id": payload.organization_id,
                "product_id": strategy.product_id,
                "strategy_id": strategy.id,
                "objective": payload.objective or strategy.marketing_objective,
                "key_message": payload.key_message or strategy.core_message,
                "proof_requirements": proof_requirements,
                "cta_strategy": cta_strategy,
                "proof_points": payload.proof_points or proof_requirements,
                "cta": payload.cta or cta_strategy,
            }
        )
        return self._save(CreativeBrief(**values))

    def create_channel_fit(self, payload: CreativeChannelFitCreate) -> CreativeChannelFit:
        if not reference_belongs_to_organization(
            self.session,
            table_name="products",
            reference_id=payload.product_id,
            organization_id=payload.organization_id,
        ):
            raise DecisionScopeError("Product was not found in this organization.")
        return self._save(CreativeChannelFit(**payload.model_dump()))

    def create_experiment(self, payload: CreativeExperimentCreate) -> CreativeExperiment:
        scoped_hypothesis(self.session, payload.hypothesis_id, payload.organization_id)
        return self._save(
            CreativeExperiment(
                **payload.model_dump(), status=CreativeExperimentStatus.PLANNED, result=None
            )
        )

    def transition_experiment(
        self, experiment: CreativeExperiment, payload: CreativeExperimentUpdate
    ) -> CreativeExperiment:
        if payload.status not in EXPERIMENT_TRANSITIONS[str(experiment.status)]:
            message = f"Creative experiment cannot transition from {experiment.status}"
            raise DecisionStateError(f"{message} to {payload.status}.")
        if payload.status == "completed" and not payload.result:
            raise DecisionStateError("A completed creative experiment requires a result.")
        experiment.status = CreativeExperimentStatus(payload.status)
        experiment.result = payload.result
        return self._save(experiment)

    def _save(self, value: EntityT) -> EntityT:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value
