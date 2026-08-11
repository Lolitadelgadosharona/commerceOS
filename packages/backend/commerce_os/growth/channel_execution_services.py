from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.growth.channel_execution_models import (
    ChannelExecutionPlan,
    ChannelPerformanceObservation,
    CreativeChannelExperiment,
    DistributionRecord,
)
from commerce_os.growth.channel_execution_schemas import (
    DistributionCreate,
    DistributionUpdate,
    ExperimentCreate,
    ExperimentUpdate,
    PerformanceCreate,
    PlanCreate,
    PlanUpdate,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
PLAN_TRANSITIONS = {
    "draft": {"ready", "cancelled"},
    "ready": {"approved", "cancelled"},
    "approved": {"active", "cancelled"},
    "active": {"paused", "completed", "cancelled"},
    "paused": {"active", "completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
EXPERIMENT_TRANSITIONS = {
    "draft": {"ready", "cancelled"},
    "ready": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
DISTRIBUTION_TRANSITIONS = {
    "draft": {"ready"},
    "ready": {"approved"},
    "approved": {"published", "paused"},
    "published": {"paused", "completed"},
    "paused": {"published", "completed"},
    "completed": set(),
}


class ChannelExecutionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_plan(self, payload: PlanCreate) -> ChannelExecutionPlan:
        self._reference("projects", payload.project_id, payload.organization_id, "Project")
        self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        self._reference("users", payload.created_by, payload.organization_id, "Creator")
        return self._save(
            ChannelExecutionPlan(**payload.model_dump(), status="draft", approval_request_id=None)
        )

    def update_plan(
        self, entity: ChannelExecutionPlan, payload: PlanUpdate
    ) -> ChannelExecutionPlan:
        if payload.objective is not None:
            entity.objective = payload.objective
        if payload.target_audience is not None:
            entity.target_audience = payload.target_audience
        if payload.status is not None:
            if payload.status not in PLAN_TRANSITIONS[entity.status]:
                raise GrowthError(
                    "Channel execution plan cannot transition "
                    f"from {entity.status} to {payload.status}."
                )
            if payload.status == "approved":
                self._approval(
                    entity,
                    payload.approval_request_id,
                    "channel_execution_plan",
                    "approve_channel_execution",
                )
                entity.approval_request_id = payload.approval_request_id
            entity.status = payload.status
        return self._save(entity)

    def create_experiment(self, payload: ExperimentCreate) -> CreativeChannelExperiment:
        plan = self.scoped(
            ChannelExecutionPlan, payload.channel_execution_plan_id, payload.organization_id
        )
        versions = Base.metadata.tables["creative_asset_versions"]
        for version_id in payload.creative_variant_ids:
            found = self.session.execute(
                select(versions.c.id).where(
                    versions.c.id == version_id,
                    versions.c.organization_id == payload.organization_id,
                    versions.c.asset_id == plan.creative_asset_id,
                )
            ).scalar_one_or_none()
            if found is None:
                raise GrowthError("Creative variant was not found for the plan asset.", "not_found")
        values = payload.model_dump(exclude={"creative_variant_ids"})
        return self._save(
            CreativeChannelExperiment(
                **values,
                creative_variant_ids=[str(item) for item in payload.creative_variant_ids],
                status="draft",
            )
        )

    def update_experiment(
        self, entity: CreativeChannelExperiment, payload: ExperimentUpdate
    ) -> CreativeChannelExperiment:
        for field in ("hypothesis", "success_metrics", "test_notes"):
            value = getattr(payload, field)
            if value is not None:
                setattr(entity, field, value)
        if payload.status is not None:
            if payload.status not in EXPERIMENT_TRANSITIONS[entity.status]:
                raise GrowthError(
                    f"Experiment cannot transition from {entity.status} to {payload.status}."
                )
            entity.status = payload.status
        return self._save(entity)

    def create_distribution(self, payload: DistributionCreate) -> DistributionRecord:
        self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        return self._save(
            DistributionRecord(
                **payload.model_dump(),
                distribution_status="draft",
                published_reference=None,
                actual_time=None,
                approval_request_id=None,
            )
        )

    def update_distribution(
        self, entity: DistributionRecord, payload: DistributionUpdate
    ) -> DistributionRecord:
        if payload.distribution_status is not None:
            target = payload.distribution_status
            if target not in DISTRIBUTION_TRANSITIONS[entity.distribution_status]:
                raise GrowthError(
                    f"Distribution cannot transition from {entity.distribution_status} to {target}."
                )
            if target == "approved":
                self._approval(
                    entity,
                    payload.approval_request_id,
                    "distribution_record",
                    "approve_distribution",
                )
                entity.approval_request_id = payload.approval_request_id
            if target == "published":
                self._approval(
                    entity,
                    entity.approval_request_id,
                    "distribution_record",
                    "approve_distribution",
                )
                if not payload.published_reference:
                    raise GrowthError(
                        "Published distribution records require a supplied reference."
                    )
            entity.distribution_status = target
        for field in ("published_reference", "scheduled_time", "actual_time"):
            value = getattr(payload, field)
            if value is not None:
                setattr(entity, field, value)
        return self._save(entity)

    def create_performance(self, payload: PerformanceCreate) -> ChannelPerformanceObservation:
        self._reference(
            "creative_assets", payload.creative_asset_id, payload.organization_id, "Creative asset"
        )
        if payload.experiment_id is not None:
            experiment = self.scoped(
                CreativeChannelExperiment, payload.experiment_id, payload.organization_id
            )
            plan = self.scoped(
                ChannelExecutionPlan, experiment.channel_execution_plan_id, payload.organization_id
            )
            if (
                plan.creative_asset_id != payload.creative_asset_id
                or plan.channel != payload.channel
            ):
                raise GrowthError("Performance observation does not match the experiment plan.")
        values = payload.model_dump(exclude={"metric_value"})
        return self._save(
            ChannelPerformanceObservation(
                **values, metric_value=self._decimal(payload.metric_value)
            )
        )

    def scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
            raise GrowthError("Growth record was not found in this organization.", "not_found")
        return entity

    def _approval(
        self,
        entity: ChannelExecutionPlan | DistributionRecord,
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

    def _reference(self, table: str, entity_id: UUID, organization_id: UUID, label: str) -> None:
        if not reference_belongs_to_organization(
            self.session, table_name=table, reference_id=entity_id, organization_id=organization_id
        ):
            raise GrowthError(f"{label} was not found in this organization.", "not_found")

    @staticmethod
    def _decimal(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
