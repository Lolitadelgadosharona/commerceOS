from datetime import UTC, date, datetime
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import OutreachTrackingEvent
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_launch_models import (
    CustomerLifecycleEvent,
    PaymentReadinessRecord,
    ProspectRevenuePipeline,
    RevenueOfferTracking,
)
from commerce_os.growth.revenue_launch_schemas import (
    CustomerLifecycleEventCreate,
    PaymentReadinessCreate,
    RevenueCommandCenter,
    RevenueOfferCreate,
    RevenuePipelineCreate,
)
from commerce_os.growth.revenue_models import (
    GrowthGift,
    GrowthOfferRecommendation,
    GrowthOutreachDraft,
    GrowthProspect,
)
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
PIPELINE_STAGES = [
    "new_prospect",
    "qualified",
    "gift_ready",
    "approved",
    "sent",
    "reply_received",
    "conversation",
    "proposal",
    "paid",
    "delivery",
    "subscription",
]
OFFER_TRANSITIONS = {
    "recommended": {"presented"},
    "presented": {"accepted", "rejected"},
    "accepted": set(),
    "rejected": set(),
}
PAYMENT_TRANSITIONS = {
    "not_requested": {"link_ready", "invoiced", "cancelled"},
    "link_ready": {"invoiced", "paid_observed", "failed", "cancelled"},
    "invoiced": {"paid_observed", "failed", "cancelled"},
    "failed": {"link_ready", "invoiced", "cancelled"},
    "paid_observed": set(),
    "cancelled": set(),
}


def scoped_launch(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError("Revenue launch record was not found in this organization.", "not_found")
    return entity


class RevenueLaunchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_pipeline(
        self, payload: RevenuePipelineCreate, actor_id: UUID
    ) -> ProspectRevenuePipeline:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        return self._save(
            ProspectRevenuePipeline(
                **payload.model_dump(),
                stage="new_prospect",
                owner_id=actor_id,
                stage_entered_at=datetime.now(UTC),
            ),
            actor_id,
            "growthos.revenue_pipeline.created",
        )

    def transition_pipeline(
        self, entity: ProspectRevenuePipeline, stage: str, notes: str, actor_id: UUID
    ) -> ProspectRevenuePipeline:
        current_index = PIPELINE_STAGES.index(entity.stage)
        if current_index + 1 >= len(PIPELINE_STAGES) or PIPELINE_STAGES[current_index + 1] != stage:
            raise GrowthError(f"Revenue pipeline cannot transition from {entity.stage} to {stage}.")
        self._validate_stage_evidence(entity, stage)
        previous = entity.stage
        entity.stage = stage
        entity.stage_entered_at = datetime.now(UTC)
        entity.notes = notes
        return self._save(
            entity,
            actor_id,
            "growthos.revenue_pipeline.transitioned",
            {"from_stage": previous, "to_stage": stage},
        )

    def create_offer(self, payload: RevenueOfferCreate, actor_id: UUID) -> RevenueOfferTracking:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if (payload.price is None) != (payload.currency is None):
            raise GrowthError("Offer price and currency must be supplied together or both unknown.")
        if payload.recommendation_id is not None:
            recommendation = scoped_revenue(
                self.session,
                GrowthOfferRecommendation,
                payload.recommendation_id,
                payload.organization_id,
            )
            if recommendation.prospect_id != payload.prospect_id:
                raise GrowthError("Offer recommendation must belong to the selected prospect.")
        return self._save(
            RevenueOfferTracking(
                **payload.model_dump(), customer_response=None, status="recommended"
            ),
            actor_id,
            "growthos.revenue_offer.created",
        )

    def transition_offer(
        self, entity: RevenueOfferTracking, status: str, response: str, actor_id: UUID
    ) -> RevenueOfferTracking:
        if status not in OFFER_TRANSITIONS[entity.status]:
            raise GrowthError(f"Revenue offer cannot transition from {entity.status} to {status}.")
        entity.status = status
        entity.customer_response = response
        return self._save(entity, actor_id, f"growthos.revenue_offer.{status}")

    def create_payment_readiness(
        self, payload: PaymentReadinessCreate, actor_id: UUID
    ) -> PaymentReadinessRecord:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        offer = scoped_launch(
            self.session, RevenueOfferTracking, payload.offer_tracking_id, payload.organization_id
        )
        if offer.prospect_id != payload.prospect_id:
            raise GrowthError("Payment readiness offer must belong to the selected prospect.")
        if offer.status != "accepted":
            raise GrowthError("Payment readiness requires a customer-accepted offer.")
        return self._save(
            PaymentReadinessRecord(
                **payload.model_dump(),
                payment_status="not_requested",
                revenue_observation_id=None,
            ),
            actor_id,
            "growthos.payment_readiness.created",
        )

    def transition_payment(
        self,
        entity: PaymentReadinessRecord,
        status: str,
        revenue_observation_id: UUID | None,
        actor_id: UUID,
    ) -> PaymentReadinessRecord:
        if status not in PAYMENT_TRANSITIONS[entity.payment_status]:
            raise GrowthError(
                f"Payment readiness cannot transition from {entity.payment_status} to {status}."
            )
        if status == "paid_observed":
            if revenue_observation_id is None:
                raise GrowthError("Paid status requires a Finance revenue observation.")
            table = Base.metadata.tables["revenue_observations"]
            observed = self.session.execute(
                table.select().where(
                    table.c.id == revenue_observation_id,
                    table.c.organization_id == entity.organization_id,
                )
            ).first()
            if observed is None:
                raise GrowthError("Finance revenue observation was not found in this organization.")
            entity.revenue_observation_id = revenue_observation_id
        elif revenue_observation_id is not None:
            raise GrowthError("Only paid status may reference Finance revenue truth.")
        entity.payment_status = status
        return self._save(entity, actor_id, f"growthos.payment_readiness.{status}")

    def create_lifecycle_event(
        self, payload: CustomerLifecycleEventCreate, actor_id: UUID
    ) -> CustomerLifecycleEvent:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if payload.lifecycle_type == "first_purchase":
            paid = self.session.scalar(
                select(func.count())
                .select_from(PaymentReadinessRecord)
                .where(
                    PaymentReadinessRecord.organization_id == payload.organization_id,
                    PaymentReadinessRecord.prospect_id == payload.prospect_id,
                    PaymentReadinessRecord.payment_status == "paid_observed",
                )
            )
            if not paid:
                raise GrowthError("First purchase requires an observed Finance revenue record.")
        values = payload.model_dump(exclude={"metadata"})
        return self._save(
            CustomerLifecycleEvent(**values, event_metadata=payload.metadata, recorded_by=actor_id),
            actor_id,
            f"growthos.customer_lifecycle.{payload.lifecycle_type}",
        )

    def command_center(self, organization_id: UUID, dashboard_date: date) -> RevenueCommandCenter:
        def count(model: type[EntityT], *criteria: Any) -> int:
            mapped = cast(Any, model)
            return int(
                self.session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(mapped.organization_id == organization_id, *criteria)
                )
                or 0
            )

        daily = Base.metadata.tables["daily_growth_opportunities"]
        rankings = Base.metadata.tables["growth_prospect_rankings"]
        todays_opportunities = int(
            self.session.execute(
                select(func.count())
                .select_from(daily)
                .where(
                    daily.c.organization_id == organization_id,
                    daily.c.queue_date == dashboard_date,
                )
            ).scalar_one()
            or 0
        )
        priority_prospects = int(
            self.session.execute(
                select(func.count())
                .select_from(rankings)
                .where(
                    rankings.c.organization_id == organization_id,
                    rankings.c.score.is_not(None),
                    rankings.c.score >= 70,
                )
            ).scalar_one()
            or 0
        )
        pipelines = list(
            self.session.scalars(
                select(ProspectRevenuePipeline).where(
                    ProspectRevenuePipeline.organization_id == organization_id
                )
            )
        )
        return RevenueCommandCenter(
            organization_id=organization_id,
            dashboard_date=dashboard_date,
            todays_opportunities=todays_opportunities,
            priority_prospects=priority_prospects,
            growth_gifts_ready=count(
                GrowthGift,
                GrowthGift.status.in_(["approved", "ready_for_delivery"]),
            ),
            pending_approvals=count(GrowthGift, GrowthGift.status == "review")
            + count(GrowthOutreachDraft, GrowthOutreachDraft.status == "human_review"),
            sent_outreach=count(
                OutreachTrackingEvent, OutreachTrackingEvent.event_type == "sent_manually"
            ),
            customer_replies=count(
                OutreachTrackingEvent, OutreachTrackingEvent.event_type == "reply_received"
            ),
            pipeline_by_stage={
                stage: sum(item.stage == stage for item in pipelines) for stage in PIPELINE_STAGES
            },
            paid_customers=count(
                PaymentReadinessRecord,
                PaymentReadinessRecord.payment_status == "paid_observed",
            ),
        )

    def _validate_stage_evidence(self, pipeline: ProspectRevenuePipeline, stage: str) -> None:
        organization_id = pipeline.organization_id
        prospect_id = pipeline.prospect_id
        if stage == "gift_ready" and not self._exists(
            GrowthGift,
            organization_id,
            prospect_id,
            GrowthGift.status.in_(["draft", "review", "approved", "ready_for_delivery"]),
        ):
            raise GrowthError("Gift Ready requires an existing Growth Gift.")
        if stage == "approved" and not self._exists(
            GrowthGift,
            organization_id,
            prospect_id,
            GrowthGift.status.in_(["approved", "ready_for_delivery"]),
        ):
            raise GrowthError("Approved stage requires a human-approved Growth Gift.")
        event_for_stage = {"sent": "sent_manually", "reply_received": "reply_received"}
        if stage in event_for_stage:
            links = Base.metadata.tables["prospect_experiment_links"]
            events = Base.metadata.tables["outreach_tracking_events"]
            found = self.session.execute(
                select(events.c.id)
                .select_from(events.join(links, events.c.prospect_experiment_link_id == links.c.id))
                .where(
                    events.c.organization_id == organization_id,
                    links.c.prospect_id == prospect_id,
                    events.c.event_type == event_for_stage[stage],
                )
            ).first()
            if found is None:
                raise GrowthError(f"{stage} stage requires its append-only outreach event.")
        if stage == "proposal" and not self._exists(
            RevenueOfferTracking,
            organization_id,
            prospect_id,
            RevenueOfferTracking.status.in_(["presented", "accepted"]),
        ):
            raise GrowthError("Proposal stage requires a presented offer.")
        if stage == "paid" and not self._exists(
            PaymentReadinessRecord,
            organization_id,
            prospect_id,
            PaymentReadinessRecord.payment_status == "paid_observed",
        ):
            raise GrowthError("Paid stage requires a Finance-backed payment observation.")
        lifecycle_required = {"delivery": "delivery", "subscription": "subscription_possible"}
        if stage in lifecycle_required and not self._exists(
            CustomerLifecycleEvent,
            organization_id,
            prospect_id,
            CustomerLifecycleEvent.lifecycle_type == lifecycle_required[stage],
        ):
            raise GrowthError(f"{stage} stage requires its lifecycle observation.")

    def _exists(
        self, model: type[EntityT], organization_id: UUID, prospect_id: UUID, criterion: Any
    ) -> bool:
        mapped = cast(Any, model)
        return bool(
            self.session.scalar(
                select(func.count())
                .select_from(model)
                .where(
                    mapped.organization_id == organization_id,
                    mapped.prospect_id == prospect_id,
                    criterion,
                )
            )
        )

    def _save(
        self,
        entity: EntityT,
        actor_id: UUID,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none", **(metadata or {})},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
