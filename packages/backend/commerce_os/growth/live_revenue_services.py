from collections import Counter
from datetime import UTC, datetime
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import ProspectExperimentLink, RevenueExperiment
from commerce_os.growth.activation_services import scoped_activation
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.live_revenue_models import (
    CustomerDeliveryItem,
    CustomerServiceDelivery,
    DailyRevenueRun,
    DailyRevenueRunProspect,
    FounderActionItem,
    GrowthExternalDataConnector,
)
from commerce_os.growth.live_revenue_schemas import (
    CustomerDeliveryCreate,
    DailyRevenueRunCreate,
    DailyRunProspectAdd,
    DeliveryItemCreate,
    FounderActionCreate,
    GrowthConnectorCreate,
    LiveRevenueExperimentAnalytics,
)
from commerce_os.growth.revenue_launch_models import RevenueOfferTracking
from commerce_os.growth.revenue_launch_services import scoped_launch
from commerce_os.growth.revenue_models import GrowthGift, GrowthProspect
from commerce_os.growth.revenue_operations_models import (
    DailyExperimentWorkspaceItem,
    GrowthCustomerFeedback,
)
from commerce_os.growth.revenue_operations_services import RevenueOperationsService
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
RUN_TRANSITIONS = {
    "draft": {"ready_for_review", "rejected"},
    "ready_for_review": {"approved", "rejected"},
    "approved": {"completed"},
    "rejected": set(),
    "completed": set(),
}
ACTION_TRANSITIONS = {
    "pending": {"approved", "rejected", "assigned"},
    "assigned": {"approved", "rejected", "completed"},
    "approved": {"completed"},
    "rejected": set(),
    "completed": set(),
}
CONNECTOR_TRANSITIONS = {
    "draft": {"configured", "disabled"},
    "configured": {"ready", "disabled"},
    "ready": {"disabled"},
    "disabled": {"configured"},
}
DELIVERY_TRANSITIONS = {
    "planned": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
ITEM_TRANSITIONS = {
    "pending": {"in_progress", "blocked", "completed", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
ACTION_SOURCE_TABLES = {
    "daily_workspace": "daily_experiment_workspace_items",
    "growth_gift": "growth_gifts",
    "customer_feedback": "growth_customer_feedback",
    "revenue_offer": "revenue_offer_tracking",
    "delivery_item": "customer_delivery_items",
}


def scoped_live(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError("Live revenue record was not found in this organization.", "not_found")
    return entity


class LiveRevenueService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, payload: DailyRevenueRunCreate, actor_id: UUID) -> DailyRevenueRun:
        scoped_activation(
            self.session, RevenueExperiment, payload.revenue_experiment_id, payload.organization_id
        )
        return self._save(
            DailyRevenueRun(
                **payload.model_dump(),
                generated_prospects=0,
                review_status="draft",
                created_by=actor_id,
                reviewed_by=None,
            ),
            actor_id,
            "growthos.daily_revenue_run.created",
        )

    def add_run_prospect(
        self, run: DailyRevenueRun, payload: DailyRunProspectAdd, actor_id: UUID
    ) -> DailyRevenueRunProspect:
        if run.review_status != "draft":
            raise GrowthError("Prospects may only be added while a daily run is draft.")
        prospect = scoped_revenue(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        assignment = self.session.scalar(
            select(ProspectExperimentLink.id).where(
                ProspectExperimentLink.organization_id == payload.organization_id,
                ProspectExperimentLink.experiment_id == run.revenue_experiment_id,
                ProspectExperimentLink.prospect_id == prospect.id,
            )
        )
        if assignment is None:
            raise GrowthError("Daily run prospects must be assigned to the revenue experiment.")
        item = DailyRevenueRunProspect(daily_revenue_run_id=run.id, **payload.model_dump())
        self.session.add(item)
        run.generated_prospects += 1
        return cast(
            DailyRevenueRunProspect,
            self._commit_pair(item, run, actor_id, "growthos.daily_revenue_run.prospect_added"),
        )

    def transition_run(self, run: DailyRevenueRun, status: str, actor_id: UUID) -> DailyRevenueRun:
        if status not in RUN_TRANSITIONS[run.review_status]:
            raise GrowthError(f"Daily run cannot transition from {run.review_status} to {status}.")
        if status == "ready_for_review" and run.generated_prospects == 0:
            raise GrowthError("A daily run requires at least one evidence-backed prospect.")
        run.review_status = status
        if status in {"approved", "rejected", "completed"}:
            run.reviewed_by = actor_id
        return self._save(run, actor_id, f"growthos.daily_revenue_run.{status}")

    def create_action(self, payload: FounderActionCreate, actor_id: UUID) -> FounderActionItem:
        if payload.revenue_experiment_id is not None:
            scoped_activation(
                self.session,
                RevenueExperiment,
                payload.revenue_experiment_id,
                payload.organization_id,
            )
        if payload.prospect_id is not None:
            scoped_revenue(
                self.session, GrowthProspect, payload.prospect_id, payload.organization_id
            )
        table = Base.metadata.tables[ACTION_SOURCE_TABLES[payload.source_type]]
        source = self.session.execute(
            table.select().where(
                table.c.id == payload.source_reference_id,
                table.c.organization_id == payload.organization_id,
            )
        ).first()
        if source is None:
            raise GrowthError("Action source was not found in this organization.")
        source_values = source._mapping
        if (
            payload.prospect_id is not None
            and "prospect_id" in source_values
            and source_values["prospect_id"] != payload.prospect_id
        ):
            raise GrowthError("Action source must belong to the selected prospect.")
        if (
            payload.revenue_experiment_id is not None
            and "revenue_experiment_id" in source_values
            and source_values["revenue_experiment_id"] != payload.revenue_experiment_id
        ):
            raise GrowthError("Action source must belong to the selected experiment.")
        return self._save(
            FounderActionItem(
                **payload.model_dump(),
                status="pending",
                assigned_to=None,
                completed_at=None,
                decision_notes="",
            ),
            actor_id,
            "growthos.founder_action.created",
        )

    def decide_action(
        self,
        item: FounderActionItem,
        action: str,
        assigned_to: UUID | None,
        notes: str,
        actor_id: UUID,
    ) -> FounderActionItem:
        status = {
            "approve": "approved",
            "reject": "rejected",
            "assign": "assigned",
            "complete": "completed",
        }[action]
        if status not in ACTION_TRANSITIONS[item.status]:
            raise GrowthError(f"Founder action cannot transition from {item.status} to {status}.")
        if assigned_to is not None:
            users = Base.metadata.tables["users"]
            user = self.session.execute(
                select(users.c.id).where(
                    users.c.id == assigned_to,
                    users.c.organization_id == item.organization_id,
                    users.c.status == "active",
                )
            ).first()
            if user is None:
                raise GrowthError("Assigned user must be active in this organization.")
            item.assigned_to = assigned_to
        item.status = status
        item.decision_notes = notes
        item.completed_at = datetime.now(UTC) if status == "completed" else None
        return self._save(item, actor_id, f"growthos.founder_action.{status}")

    def create_connector(
        self, payload: GrowthConnectorCreate, actor_id: UUID
    ) -> GrowthExternalDataConnector:
        self._reject_secrets(payload.configuration)
        values = payload.model_dump(exclude={"configuration"})
        return self._save(
            GrowthExternalDataConnector(
                **values, configuration_metadata=payload.configuration, status="draft"
            ),
            actor_id,
            "growthos.external_connector.created",
        )

    def transition_connector(
        self, connector: GrowthExternalDataConnector, status: str, actor_id: UUID
    ) -> GrowthExternalDataConnector:
        if status not in CONNECTOR_TRANSITIONS[connector.status]:
            raise GrowthError(f"Connector cannot transition from {connector.status} to {status}.")
        if (
            status == "ready"
            and connector.collection_mode == "controlled_connector"
            and connector.credential_reference is None
        ):
            raise GrowthError(
                "Controlled connector readiness requires an external credential reference."
            )
        connector.status = status
        return self._save(connector, actor_id, f"growthos.external_connector.{status}")

    def create_delivery(
        self, payload: CustomerDeliveryCreate, actor_id: UUID
    ) -> CustomerServiceDelivery:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        offer = scoped_launch(
            self.session, RevenueOfferTracking, payload.offer_tracking_id, payload.organization_id
        )
        if offer.prospect_id != payload.prospect_id or offer.status != "accepted":
            raise GrowthError("Service delivery requires the prospect's accepted offer.")
        payments = Base.metadata.tables["payment_readiness_records"]
        paid = self.session.execute(
            select(payments.c.id).where(
                payments.c.organization_id == payload.organization_id,
                payments.c.offer_tracking_id == offer.id,
                payments.c.payment_status == "paid_observed",
                payments.c.revenue_observation_id.is_not(None),
            )
        ).first()
        if paid is None:
            raise GrowthError("Service delivery requires Finance-backed paid revenue.")
        return self._save(
            CustomerServiceDelivery(
                **payload.model_dump(),
                status="planned",
                owner_id=actor_id,
                started_at=None,
                completed_at=None,
                customer_feedback_reference=None,
            ),
            actor_id,
            "growthos.customer_delivery.created",
        )

    def transition_delivery(
        self,
        delivery: CustomerServiceDelivery,
        status: str,
        feedback_reference: str | None,
        actor_id: UUID,
    ) -> CustomerServiceDelivery:
        if status not in DELIVERY_TRANSITIONS[delivery.status]:
            raise GrowthError(f"Delivery cannot transition from {delivery.status} to {status}.")
        if status == "completed":
            incomplete = self.session.scalar(
                select(func.count())
                .select_from(CustomerDeliveryItem)
                .where(
                    CustomerDeliveryItem.organization_id == delivery.organization_id,
                    CustomerDeliveryItem.delivery_id == delivery.id,
                    CustomerDeliveryItem.item_type.in_(["checklist", "milestone"]),
                    CustomerDeliveryItem.status != "completed",
                )
            )
            if incomplete:
                raise GrowthError(
                    "Delivery completion requires all checklist and milestone items completed."
                )
        delivery.status = status
        delivery.customer_feedback_reference = (
            feedback_reference or delivery.customer_feedback_reference
        )
        if status == "in_progress" and delivery.started_at is None:
            delivery.started_at = datetime.now(UTC)
        delivery.completed_at = datetime.now(UTC) if status == "completed" else None
        return self._save(delivery, actor_id, f"growthos.customer_delivery.{status}")

    def create_delivery_item(
        self, delivery: CustomerServiceDelivery, payload: DeliveryItemCreate, actor_id: UUID
    ) -> CustomerDeliveryItem:
        if delivery.status in {"completed", "cancelled"}:
            raise GrowthError("Items cannot be added to a closed delivery.")
        return self._save(
            CustomerDeliveryItem(
                delivery_id=delivery.id, **payload.model_dump(), status="pending", completed_at=None
            ),
            actor_id,
            "growthos.customer_delivery_item.created",
        )

    def transition_delivery_item(
        self,
        item: CustomerDeliveryItem,
        status: str,
        evidence_reference: str | None,
        actor_id: UUID,
    ) -> CustomerDeliveryItem:
        if status not in ITEM_TRANSITIONS[item.status]:
            raise GrowthError(f"Delivery item cannot transition from {item.status} to {status}.")
        if (
            item.item_type in {"customer_feedback", "expansion_opportunity"}
            and status == "completed"
            and not (evidence_reference or item.evidence_reference)
        ):
            raise GrowthError("Feedback and expansion completion require an evidence reference.")
        item.status = status
        item.evidence_reference = evidence_reference or item.evidence_reference
        item.completed_at = datetime.now(UTC) if status == "completed" else None
        return self._save(item, actor_id, f"growthos.customer_delivery_item.{status}")

    def analytics(
        self, experiment_id: UUID, organization_id: UUID
    ) -> LiveRevenueExperimentAnalytics:
        base = RevenueOperationsService(self.session).dashboard(experiment_id, organization_id)
        links = list(
            self.session.scalars(
                select(ProspectExperimentLink).where(
                    ProspectExperimentLink.organization_id == organization_id,
                    ProspectExperimentLink.experiment_id == experiment_id,
                )
            )
        )
        prospect_ids = [link.prospect_id for link in links]
        if not prospect_ids:
            return LiveRevenueExperimentAnalytics(
                organization_id=organization_id,
                revenue_experiment_id=experiment_id,
                prospects_reviewed=0,
                gifts_approved=0,
                outreach_sent=0,
                replies=0,
                positive_replies=0,
                offers=0,
                paid_customers=0,
                paid_revenue=base.revenue,
                revenue_currency=base.revenue_currency,
                lost_reasons={},
            )
        feedback = list(
            self.session.scalars(
                select(GrowthCustomerFeedback).where(
                    GrowthCustomerFeedback.organization_id == organization_id,
                    GrowthCustomerFeedback.revenue_experiment_id == experiment_id,
                )
            )
        )
        lost = Counter(item.reason_lost for item in feedback if item.reason_lost)
        return LiveRevenueExperimentAnalytics(
            organization_id=organization_id,
            revenue_experiment_id=experiment_id,
            prospects_reviewed=self._count(
                DailyExperimentWorkspaceItem,
                organization_id,
                DailyExperimentWorkspaceItem.revenue_experiment_id == experiment_id,
                DailyExperimentWorkspaceItem.status != "pending_review",
            ),
            gifts_approved=self._count(
                GrowthGift,
                organization_id,
                GrowthGift.prospect_id.in_(prospect_ids),
                GrowthGift.status.in_(["approved", "ready_for_delivery"]),
            ),
            outreach_sent=base.outreach_sent,
            replies=base.replies,
            positive_replies=base.positive_conversations,
            offers=base.offers,
            paid_customers=base.paid_customers,
            paid_revenue=base.revenue,
            revenue_currency=base.revenue_currency,
            lost_reasons=dict(lost),
        )

    @staticmethod
    def _reject_secrets(configuration: dict[str, Any]) -> None:
        forbidden = {"password", "token", "secret", "authorization", "api_key", "cookie"}
        if any(str(key).casefold() in forbidden for key in configuration):
            raise GrowthError("Connector configuration cannot contain credentials or secrets.")

    def _count(self, model: Any, organization_id: UUID, *criteria: Any) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.organization_id == organization_id, *criteria)
            )
            or 0
        )

    def _commit_pair(
        self, entity: EntityT, parent: EntityT, actor_id: UUID, action: str
    ) -> EntityT:
        self.session.flush()
        self._audit(entity, actor_id, action)
        self.session.commit()
        self.session.refresh(entity)
        self.session.refresh(parent)
        return entity

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        self._audit(entity, actor_id, action)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def _audit(self, entity: EntityT, actor_id: UUID, action: str) -> None:
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
