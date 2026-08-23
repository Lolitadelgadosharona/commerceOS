from decimal import Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import (
    OutreachTrackingEvent,
    ProspectExperimentLink,
    RevenueExperiment,
)
from commerce_os.growth.activation_services import scoped_activation
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_launch_models import (
    PaymentReadinessRecord,
    RevenueOfferTracking,
)
from commerce_os.growth.revenue_models import (
    GrowthDiagnosis,
    GrowthGift,
    GrowthOfferRecommendation,
    GrowthOutreachDraft,
    GrowthProspect,
    SalesConversationAnalysis,
)
from commerce_os.growth.revenue_operations_models import (
    DailyExperimentWorkspaceItem,
    EmailWorkflowReference,
    GrowthCustomerFeedback,
)
from commerce_os.growth.revenue_operations_schemas import (
    CustomerFeedbackCreate,
    EmailWorkflowReferenceCreate,
    RevenueExperimentOperationsDashboard,
    WorkspaceItemCreate,
)
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
WORKSPACE_TRANSITIONS = {
    "pending_review": {"approved", "rejected", "saved_for_later"},
    "saved_for_later": {"approved", "rejected", "saved_for_later"},
    "approved": set(),
    "rejected": set(),
}
FEEDBACK_TRANSITIONS = {
    "draft": {"reviewed", "rejected"},
    "reviewed": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
}


def scoped_operations(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError(
            "Revenue operations record was not found in this organization.", "not_found"
        )
    return entity


class RevenueOperationsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_workspace_item(
        self, payload: WorkspaceItemCreate, actor_id: UUID
    ) -> DailyExperimentWorkspaceItem:
        experiment = scoped_activation(
            self.session, RevenueExperiment, payload.revenue_experiment_id, payload.organization_id
        )
        prospect = scoped_revenue(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        assignment = self.session.scalar(
            select(ProspectExperimentLink).where(
                ProspectExperimentLink.organization_id == payload.organization_id,
                ProspectExperimentLink.experiment_id == experiment.id,
                ProspectExperimentLink.prospect_id == prospect.id,
            )
        )
        if assignment is None:
            raise GrowthError("Daily workspace prospect must be assigned to the experiment.")
        self._validate_optional_prospect_ref(
            "daily_growth_opportunities", payload.daily_opportunity_id, payload, "prospect_id"
        )
        for model, entity_id, label in [
            (GrowthDiagnosis, payload.diagnosis_id, "Diagnosis"),
            (GrowthGift, payload.growth_gift_id, "Growth Gift"),
            (GrowthOfferRecommendation, payload.offer_recommendation_id, "Offer recommendation"),
        ]:
            if entity_id is not None:
                record = scoped_revenue(self.session, model, entity_id, payload.organization_id)
                if record.prospect_id != payload.prospect_id:  # type: ignore[attr-defined]
                    raise GrowthError(f"{label} must belong to the workspace prospect.")
        return self._save(
            DailyExperimentWorkspaceItem(
                **payload.model_dump(),
                status="pending_review",
                review_notes="",
                reviewed_by=None,
            ),
            actor_id,
            "growthos.daily_workspace.created",
        )

    def decide_workspace_item(
        self, entity: DailyExperimentWorkspaceItem, action: str, notes: str, actor_id: UUID
    ) -> DailyExperimentWorkspaceItem:
        status = {"approve": "approved", "reject": "rejected", "save_for_later": "saved_for_later"}[
            action
        ]
        if status not in WORKSPACE_TRANSITIONS[entity.status]:
            raise GrowthError(f"Workspace item cannot transition from {entity.status} to {status}.")
        entity.status = status
        entity.review_notes = notes
        entity.reviewed_by = actor_id
        return self._save(
            entity,
            actor_id,
            f"growthos.daily_workspace.{status}",
            {"founder_action": action},
        )

    def create_email_reference(
        self, payload: EmailWorkflowReferenceCreate, actor_id: UUID
    ) -> EmailWorkflowReference:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if payload.outreach_draft_id is not None:
            draft = scoped_revenue(
                self.session,
                GrowthOutreachDraft,
                payload.outreach_draft_id,
                payload.organization_id,
            )
            if draft.prospect_id != payload.prospect_id:
                raise GrowthError("Email workflow draft must belong to the selected prospect.")
        self._reject_secret_like_metadata(payload.metadata)
        values = payload.model_dump(exclude={"metadata"})
        return self._save(
            EmailWorkflowReference(
                **values, reference_metadata=payload.metadata, recorded_by=actor_id
            ),
            actor_id,
            "growthos.email_reference.appended",
        )

    def create_feedback(
        self, payload: CustomerFeedbackCreate, actor_id: UUID
    ) -> GrowthCustomerFeedback:
        experiment = scoped_activation(
            self.session, RevenueExperiment, payload.revenue_experiment_id, payload.organization_id
        )
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        assignment = self.session.scalar(
            select(ProspectExperimentLink.id).where(
                ProspectExperimentLink.organization_id == payload.organization_id,
                ProspectExperimentLink.experiment_id == experiment.id,
                ProspectExperimentLink.prospect_id == payload.prospect_id,
            )
        )
        if assignment is None:
            raise GrowthError("Customer feedback prospect must be assigned to the experiment.")
        if payload.conversation_analysis_id is not None:
            analysis = scoped_revenue(
                self.session,
                SalesConversationAnalysis,
                payload.conversation_analysis_id,
                payload.organization_id,
            )
            if analysis.prospect_id != payload.prospect_id:
                raise GrowthError("Feedback analysis must belong to the selected prospect.")
        return self._save(
            GrowthCustomerFeedback(
                **payload.model_dump(),
                status="draft",
                learning_observation_id=None,
                reviewed_by=None,
            ),
            actor_id,
            "growthos.customer_feedback.created",
        )

    def decide_feedback(
        self,
        entity: GrowthCustomerFeedback,
        status: str,
        actor_id: UUID,
        learning_observation_id: UUID | None = None,
    ) -> GrowthCustomerFeedback:
        self.validate_feedback_decision(entity, status)
        if status == "approved":
            if learning_observation_id is None:
                raise GrowthError("Approved feedback requires its Learning observation.")
            table = Base.metadata.tables["learning_observations"]
            observation = self.session.execute(
                table.select().where(
                    table.c.id == learning_observation_id,
                    table.c.organization_id == entity.organization_id,
                    table.c.source_type == "growth_customer_feedback",
                    table.c.source_record_id == entity.id,
                )
            ).first()
            if observation is None:
                raise GrowthError("Learning observation does not match this feedback record.")
            entity.learning_observation_id = learning_observation_id
        entity.status = status
        entity.reviewed_by = actor_id
        return self._save(entity, actor_id, f"growthos.customer_feedback.{status}")

    @staticmethod
    def validate_feedback_decision(entity: GrowthCustomerFeedback, status: str) -> None:
        if status not in FEEDBACK_TRANSITIONS[entity.status]:
            raise GrowthError(
                f"Customer feedback cannot transition from {entity.status} to {status}."
            )

    def dashboard(
        self, experiment_id: UUID, organization_id: UUID
    ) -> RevenueExperimentOperationsDashboard:
        scoped_activation(self.session, RevenueExperiment, experiment_id, organization_id)
        links = list(
            self.session.scalars(
                select(ProspectExperimentLink).where(
                    ProspectExperimentLink.organization_id == organization_id,
                    ProspectExperimentLink.experiment_id == experiment_id,
                )
            )
        )
        prospect_ids = [item.prospect_id for item in links]
        if not prospect_ids:
            return RevenueExperimentOperationsDashboard(
                organization_id=organization_id,
                revenue_experiment_id=experiment_id,
                prospects_discovered=0,
                qualified_prospects=0,
                gifts_created=0,
                outreach_sent=0,
                replies=0,
                positive_conversations=0,
                offers=0,
                paid_customers=0,
                revenue=Decimal("0"),
                revenue_currency=None,
                estimated_ai_cost=Decimal("0"),
                ai_cost_currency=None,
            )
        link_ids = [item.id for item in links]
        qualified = self._count(
            GrowthProspect,
            organization_id,
            GrowthProspect.id.in_(prospect_ids),
            GrowthProspect.status.in_(["qualified", "contacted", "replied", "customer"]),
        )
        sent = self._count(
            OutreachTrackingEvent,
            organization_id,
            OutreachTrackingEvent.prospect_experiment_link_id.in_(link_ids),
            OutreachTrackingEvent.event_type == "sent_manually",
        )
        replies = self._count(
            OutreachTrackingEvent,
            organization_id,
            OutreachTrackingEvent.prospect_experiment_link_id.in_(link_ids),
            OutreachTrackingEvent.event_type == "reply_received",
        )
        payments = list(
            self.session.scalars(
                select(PaymentReadinessRecord).where(
                    PaymentReadinessRecord.organization_id == organization_id,
                    PaymentReadinessRecord.prospect_id.in_(prospect_ids),
                    PaymentReadinessRecord.payment_status == "paid_observed",
                )
            )
        )
        revenue, revenue_currency = self._finance_total(
            organization_id,
            [item.revenue_observation_id for item in payments if item.revenue_observation_id],
        )
        ai_cost, ai_currency = self._ai_cost(experiment_id, organization_id)
        return RevenueExperimentOperationsDashboard(
            organization_id=organization_id,
            revenue_experiment_id=experiment_id,
            prospects_discovered=len(prospect_ids),
            qualified_prospects=qualified,
            gifts_created=self._count(
                GrowthGift, organization_id, GrowthGift.prospect_id.in_(prospect_ids)
            ),
            outreach_sent=sent,
            replies=replies,
            positive_conversations=self._count(
                SalesConversationAnalysis,
                organization_id,
                SalesConversationAnalysis.prospect_id.in_(prospect_ids),
                SalesConversationAnalysis.buying_signal.in_(["positive", "strong"]),
            ),
            offers=self._count(
                RevenueOfferTracking,
                organization_id,
                RevenueOfferTracking.prospect_id.in_(prospect_ids),
            ),
            paid_customers=len({item.prospect_id for item in payments}),
            revenue=revenue,
            revenue_currency=revenue_currency,
            estimated_ai_cost=ai_cost,
            ai_cost_currency=ai_currency,
        )

    def _validate_optional_prospect_ref(
        self, table_name: str, entity_id: UUID | None, payload: WorkspaceItemCreate, column: str
    ) -> None:
        if entity_id is None:
            return
        table = Base.metadata.tables[table_name]
        row = self.session.execute(
            table.select().where(
                table.c.id == entity_id,
                table.c.organization_id == payload.organization_id,
                getattr(table.c, column) == payload.prospect_id,
            )
        ).first()
        if row is None:
            raise GrowthError("Daily opportunity must belong to the workspace prospect.")

    @staticmethod
    def _reject_secret_like_metadata(metadata: dict[str, Any]) -> None:
        forbidden = {"password", "token", "secret", "authorization", "api_key", "cookie"}
        if any(str(key).casefold() in forbidden for key in metadata):
            raise GrowthError("Email workflow metadata cannot contain credentials or secrets.")

    def _count(self, model: Any, organization_id: UUID, *criteria: Any) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.organization_id == organization_id, *criteria)
            )
            or 0
        )

    def _finance_total(
        self, organization_id: UUID, observation_ids: list[UUID]
    ) -> tuple[Decimal, str | None]:
        if not observation_ids:
            return Decimal("0"), None
        table = Base.metadata.tables["revenue_observations"]
        rows = list(
            self.session.execute(
                select(table.c.amount, table.c.currency).where(
                    table.c.organization_id == organization_id,
                    table.c.id.in_(observation_ids),
                )
            )
        )
        currencies = {row.currency for row in rows}
        if len(currencies) != 1:
            return Decimal("0"), None
        return sum((Decimal(row.amount) for row in rows), Decimal("0")), next(iter(currencies))

    def _ai_cost(self, experiment_id: UUID, organization_id: UUID) -> tuple[Decimal, str | None]:
        requests = Base.metadata.tables["ai_requests"]
        costs = Base.metadata.tables["ai_cost_observations"]
        rows = list(
            self.session.execute(
                select(costs.c.estimated_cost, costs.c.currency)
                .select_from(costs.join(requests, costs.c.related_request_id == requests.c.id))
                .where(
                    costs.c.organization_id == organization_id,
                    requests.c.context_type == "revenue_experiment",
                    requests.c.context_reference == str(experiment_id),
                )
            )
        )
        currencies = {row.currency for row in rows}
        if not rows or len(currencies) != 1:
            return Decimal("0"), None
        return sum((Decimal(row.estimated_cost) for row in rows), Decimal("0")), next(
            iter(currencies)
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
