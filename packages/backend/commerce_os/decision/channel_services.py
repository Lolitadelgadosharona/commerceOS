from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

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
    EvidenceCreate,
    MeasurementCreate,
    PathCreate,
    ScoreCreate,
    StepCreate,
    StrategyCreate,
)
from commerce_os.decision.creative_models import CreativeStrategy
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)

FACTOR_NAMES = (
    "target_customer_fit",
    "product_fit",
    "buying_intent",
    "visual_fit",
    "organic_potential",
    "search_discovery_potential",
    "content_cost",
    "competition",
    "expected_acquisition_cost",
    "historical_performance_confidence",
    "conversion_path_fit",
)
PENALTY_FACTORS = {"content_cost", "competition", "expected_acquisition_cost"}
STEP_OWNERS = {
    "content": "growth",
    "ad": "growth",
    "search_discovery": "growth",
    "community_interaction": "growth",
    "landing_page": "growth",
    "product_page": "growth",
    "checkout": "operations",
    "lead_form": "operations",
    "message": "operations",
    "qualification": "operations",
    "quote": "operations",
    "order": "operations",
}
TRANSITIONS = {
    "draft": {"recommended", "rejected", "archived"},
    "recommended": {"approved", "rejected", "archived"},
    "approved": {"archived"},
    "rejected": {"archived"},
    "archived": set(),
}


def scoped_strategy(session: Session, entity_id: UUID, organization_id: UUID) -> ChannelStrategy:
    entity = session.get(ChannelStrategy, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise DecisionScopeError("Channel strategy was not found in this organization.")
    return entity


def scoped_path(session: Session, entity_id: UUID, organization_id: UUID) -> ConversionPath:
    entity = session.get(ConversionPath, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise DecisionScopeError("Conversion path was not found in this organization.")
    return entity


class ChannelStrategyService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: StrategyCreate) -> ChannelStrategy:
        for table, value, label in (
            ("products", payload.product_id, "Product"),
            ("projects", payload.project_id, "Project"),
        ):
            if value and not reference_belongs_to_organization(
                self.session,
                table_name=table,
                reference_id=value,
                organization_id=payload.organization_id,
            ):
                raise DecisionScopeError(f"{label} was not found in this organization.")
        if payload.creative_strategy_id:
            creative = self.session.get(CreativeStrategy, payload.creative_strategy_id)
            if (
                creative is None
                or creative.organization_id != payload.organization_id
                or creative.product_id != payload.product_id
            ):
                raise DecisionScopeError(
                    "Creative strategy does not match this product and organization."
                )
        return self._save(
            ChannelStrategy(**payload.model_dump(), status=ChannelStrategyStatus.DRAFT)
        )

    def transition(
        self, strategy: ChannelStrategy, status: ChannelStrategyStatus
    ) -> ChannelStrategy:
        if status.value not in TRANSITIONS[str(strategy.status)]:
            raise DecisionStateError(
                f"Channel strategy cannot transition from {strategy.status} to {status.value}."
            )
        strategy.status = status
        return self._save(strategy)

    def create_candidate(self, payload: CandidateCreate) -> ChannelCandidate:
        scoped_strategy(self.session, payload.strategy_id, payload.organization_id)
        return self._save(ChannelCandidate(**payload.model_dump()))

    def score(self, payload: ScoreCreate) -> ChannelOpportunityScore:
        candidate = self.session.get(ChannelCandidate, payload.candidate_id)
        if candidate is None or candidate.organization_id != payload.organization_id:
            raise DecisionScopeError("Channel candidate was not found in this organization.")
        values = payload.model_dump(exclude={"organization_id", "candidate_id"})
        present = {name: value for name, value in values.items() if value is not None}
        if not present:
            raise DecisionStateError("At least one evidenced score factor is required.")
        adjusted = [
            100 - value if name in PENALTY_FACTORS else value for name, value in present.items()
        ]
        overall = round(sum(adjusted) / len(adjusted), 2)
        coverage = round(len(present) / len(FACTOR_NAMES), 4)
        score = self.session.scalar(
            select(ChannelOpportunityScore).where(
                ChannelOpportunityScore.candidate_id == payload.candidate_id
            )
        )
        data = payload.model_dump()
        if score is None:
            score = ChannelOpportunityScore(**data)
        else:
            for name, value in data.items():
                setattr(score, name, value)
        score.overall_score = overall
        score.evidence_coverage = coverage
        score.formula_version = "channel-opportunity-v1.0"
        return self._save(score)

    def create_evidence(self, payload: EvidenceCreate) -> ChannelDecisionEvidence:
        strategy = scoped_strategy(self.session, payload.strategy_id, payload.organization_id)
        if payload.evidence_type == "creative_strategy" and (
            strategy.creative_strategy_id is None
            or payload.source_reference != str(strategy.creative_strategy_id)
        ):
            raise DecisionScopeError(
                "Creative evidence must reference the linked creative strategy."
            )
        return self._save(ChannelDecisionEvidence(**payload.model_dump()))

    def create_measurement(self, payload: MeasurementCreate) -> ChannelMeasurementPlan:
        scoped_strategy(self.session, payload.strategy_id, payload.organization_id)
        return self._save(ChannelMeasurementPlan(**payload.model_dump()))

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity


class ConversionPathService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: PathCreate) -> ConversionPath:
        strategy = scoped_strategy(self.session, payload.strategy_id, payload.organization_id)
        return self._save(
            ConversionPath(
                **payload.model_dump(), business_model=strategy.business_model, status="draft"
            )
        )

    def add_step(self, payload: StepCreate) -> ConversionPathStep:
        scoped_path(self.session, payload.path_id, payload.organization_id)
        expected_owner = STEP_OWNERS[payload.step_type]
        if payload.responsible_domain != expected_owner:
            raise DecisionStateError(
                f"{payload.step_type} is owned by the {expected_owner} domain."
            )
        if payload.step_type == "ad" and not payload.approval_required:
            raise DecisionStateError("Paid advertising steps must retain an approval boundary.")
        if payload.step_type == "quote" and not payload.human_required:
            raise DecisionStateError("B2B quote steps require human authority.")
        return self._save(ConversionPathStep(**payload.model_dump()))

    def validate(self, path: ConversionPath) -> ConversionPath:
        steps = list(
            self.session.scalars(
                select(ConversionPathStep)
                .where(ConversionPathStep.path_id == path.id)
                .order_by(ConversionPathStep.sequence)
            )
        )
        types = [step.step_type for step in steps]
        required = (
            ["landing_page|product_page", "checkout", "order"]
            if path.business_model == "b2c"
            else ["lead_form|message", "qualification", "quote", "order"]
        )
        traffic = {"content", "ad", "search_discovery", "community_interaction"}
        if not types or types[0] not in traffic:
            raise DecisionStateError(
                "Conversion path must begin with an acquisition/discovery step."
            )
        cursor = 0
        for expected in required:
            choices = expected.split("|")
            positions = [
                types.index(choice, cursor) for choice in choices if choice in types[cursor:]
            ]
            if not positions:
                raise DecisionStateError(f"Conversion path requires an ordered {expected} step.")
            cursor = min(positions) + 1
        path.status = "validated"
        return self._save(path)

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
