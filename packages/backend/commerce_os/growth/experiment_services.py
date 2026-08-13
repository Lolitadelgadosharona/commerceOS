from decimal import ROUND_HALF_UP, Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.growth.errors import GrowthError
from commerce_os.growth.experiment_models import (
    DistributionCampaign,
    ExperimentVariant,
    GrowthCreativeExperiment,
    GrowthLearningObservationLink,
    GrowthLearningSignal,
    GrowthPerformanceObservation,
)
from commerce_os.growth.experiment_schemas import (
    DistributionCampaignCreate,
    ExperimentVariantCreate,
    GrowthExperimentCreate,
    GrowthLearningSignalCreate,
    GrowthPerformanceCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
EXPERIMENT_TRANSITIONS = {
    "draft": {"review", "cancelled"},
    "review": {"approved", "cancelled"},
    "approved": {"active", "cancelled"},
    "active": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
CAMPAIGN_TRANSITIONS = {
    "draft": {"review", "cancelled"},
    "review": {"approved", "cancelled"},
    "approved": {"active", "cancelled"},
    "active": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def scoped_growth(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError("Growth record was not found in this organization.", "not_found")
    return entity


class GrowthExperimentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_experiment(
        self, payload: GrowthExperimentCreate, actor_id: UUID
    ) -> GrowthCreativeExperiment:
        self._reference("projects", payload.project_id, payload.organization_id, "Project")
        self._reference(
            "creative_strategies",
            payload.creative_strategy_id,
            payload.organization_id,
            "Creative strategy",
        )
        return self._save_audited(
            GrowthCreativeExperiment(
                **payload.model_dump(), status="draft", owner_id=actor_id, approval_request_id=None
            ),
            actor_id,
            "growth.experiment.created",
        )

    def transition_experiment(
        self,
        entity: GrowthCreativeExperiment,
        status: str,
        actor_id: UUID,
        approval_id: UUID | None = None,
    ) -> GrowthCreativeExperiment:
        if status not in EXPERIMENT_TRANSITIONS[entity.status]:
            raise GrowthError(f"Experiment cannot transition from {entity.status} to {status}.")
        if status == "approved":
            self._approval(
                entity, approval_id, "growth_creative_experiment", "approve_growth_experiment"
            )
            entity.approval_request_id = approval_id
        if status == "active" and entity.approval_request_id is None:
            raise GrowthError("Active experiments require Governance approval.")
        entity.status = status
        return self._save_audited(entity, actor_id, f"growth.experiment.{status}")

    def create_variant(self, payload: ExperimentVariantCreate, actor_id: UUID) -> ExperimentVariant:
        experiment = scoped_growth(
            self.session, GrowthCreativeExperiment, payload.experiment_id, payload.organization_id
        )
        asset = self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        if asset["review_status"] != "ready_for_distribution":
            raise GrowthError("Experiment variants require distribution-ready creative assets.")
        if experiment.status in {"completed", "cancelled"}:
            raise GrowthError("Terminal experiments cannot accept variants.")
        return self._save_audited(
            ExperimentVariant(**payload.model_dump()), actor_id, "growth.variant.created"
        )

    def create_campaign(
        self, payload: DistributionCampaignCreate, actor_id: UUID
    ) -> DistributionCampaign:
        experiment = scoped_growth(
            self.session, GrowthCreativeExperiment, payload.experiment_id, payload.organization_id
        )
        self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        if experiment.channel != payload.channel:
            raise GrowthError("Campaign channel must match its experiment.")
        return self._save_audited(
            DistributionCampaign(
                **payload.model_dump(),
                approval_state="pending",
                lifecycle_state="draft",
                approval_request_id=None,
            ),
            actor_id,
            "growth.distribution_campaign.created",
        )

    def transition_campaign(
        self,
        entity: DistributionCampaign,
        state: str,
        actor_id: UUID,
        approval_id: UUID | None = None,
    ) -> DistributionCampaign:
        if state not in CAMPAIGN_TRANSITIONS[entity.lifecycle_state]:
            raise GrowthError(
                f"Campaign cannot transition from {entity.lifecycle_state} to {state}."
            )
        if state == "approved":
            self._approval(
                entity, approval_id, "distribution_campaign", "approve_distribution_campaign"
            )
            entity.approval_request_id = approval_id
            entity.approval_state = "approved"
        if state == "active" and (
            entity.approval_state != "approved" or entity.approval_request_id is None
        ):
            raise GrowthError("Active distribution requires Governance approval.")
        entity.lifecycle_state = state
        return self._save_audited(entity, actor_id, f"growth.distribution_campaign.{state}")

    def create_performance(
        self, payload: GrowthPerformanceCreate, actor_id: UUID
    ) -> GrowthPerformanceObservation:
        experiment = scoped_growth(
            self.session, GrowthCreativeExperiment, payload.experiment_id, payload.organization_id
        )
        self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        variant = Base.metadata.tables["growth_experiment_variants"]
        linked = self.session.scalar(
            select(variant.c.id).where(
                variant.c.experiment_id == experiment.id,
                variant.c.creative_asset_id == payload.creative_asset_id,
            )
        )
        if linked is None:
            raise GrowthError("Performance asset must be an experiment variant.")
        if payload.revenue_observation_id is not None:
            self._reference(
                "revenue_observations",
                payload.revenue_observation_id,
                payload.organization_id,
                "Revenue observation",
            )
        values = payload.model_dump()
        values["engagement"] = self._decimal(payload.engagement)
        values["conversion"] = self._decimal(payload.conversion)
        return self._save_audited(
            GrowthPerformanceObservation(**values), actor_id, "growth.performance_observed"
        )

    def create_learning(
        self, payload: GrowthLearningSignalCreate, actor_id: UUID
    ) -> GrowthLearningSignal:
        experiment = scoped_growth(
            self.session,
            GrowthCreativeExperiment,
            payload.source_experiment_id,
            payload.organization_id,
        )
        observations = [
            scoped_growth(self.session, GrowthPerformanceObservation, item, payload.organization_id)
            for item in payload.observation_ids
        ]
        if any(item.experiment_id != experiment.id for item in observations):
            raise GrowthError("Learning observations must belong to the source experiment.")
        if payload.pattern_reference_id is not None:
            self._reference(
                "creative_pattern_references",
                payload.pattern_reference_id,
                payload.organization_id,
                "Creative pattern",
            )
        signal = GrowthLearningSignal(**payload.model_dump(exclude={"observation_ids"}))
        self.session.add(signal)
        self.session.flush()
        self.session.add_all(
            [
                GrowthLearningObservationLink(
                    organization_id=payload.organization_id,
                    learning_signal_id=signal.id,
                    observation_id=item.id,
                )
                for item in observations
            ]
        )
        return self._commit_audited(signal, actor_id, "growth.learning_signal.created")

    def _approval(
        self,
        entity: GrowthCreativeExperiment | DistributionCampaign,
        approval_id: UUID | None,
        object_type: str,
        action: str,
    ) -> None:
        if approval_id is None:
            raise GrowthError("This transition requires an approved Governance request.")
        table = Base.metadata.tables["approval_requests"]
        row = (
            self.session.execute(
                table.select().where(
                    table.c.id == approval_id, table.c.organization_id == entity.organization_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            row is None
            or row["status"] != "approved"
            or row["object_type"] != object_type
            or row["object_id"] != entity.id
            or row["requested_action"] != action
        ):
            raise GrowthError("Governance approval does not authorize this transition.")

    def _reference(
        self, table_name: str, entity_id: UUID, organization_id: UUID, label: str
    ) -> Any:
        table = Base.metadata.tables[table_name]
        row = (
            self.session.execute(
                table.select().where(
                    table.c.id == entity_id, table.c.organization_id == organization_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise GrowthError(f"{label} was not found in this organization.", "not_found")
        return row

    @staticmethod
    def _decimal(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _save_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        return self._commit_audited(entity, actor_id, action)

    def _commit_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        audited = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=audited.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=audited.__tablename__,
            entity_id=cast(UUID, audited.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
