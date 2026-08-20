from collections import Counter
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.revenue_conversation_models import (
    CustomerIntentJourney,
    SalesIntentSignal,
    SupportLearningSignal,
)
from commerce_os.intelligence.revenue_conversation_schemas import (
    IntentJourneyCreate,
    IntentJourneyTransition,
    JourneyDashboardRead,
    SalesIntentCreate,
    SupportLearningCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)


class RevenueConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_journey(self, payload: IntentJourneyCreate, actor_id: UUID) -> CustomerIntentJourney:
        self._customer(payload.customer_id, payload.organization_id)
        existing = self.session.scalar(
            select(CustomerIntentJourney.id).where(
                CustomerIntentJourney.organization_id == payload.organization_id,
                CustomerIntentJourney.customer_id == payload.customer_id,
            )
        )
        if existing is not None:
            raise IntelligenceScopeError("Customer already has an intent journey.")
        if payload.status != "unknown" and not payload.evidence_references:
            raise IntelligenceScopeError("A known intent stage requires evidence.")
        self._evidence(payload.evidence_references, payload.organization_id, payload.customer_id)
        return self._save(
            CustomerIntentJourney(
                organization_id=payload.organization_id,
                customer_id=payload.customer_id,
                status=payload.status,
                evidence_references=[
                    item.model_dump(mode="json") for item in payload.evidence_references
                ],
                confidence=payload.confidence,
            ),
            actor_id,
            "intelligence.intent_journey.created",
        )

    def transition_journey(
        self,
        entity: CustomerIntentJourney,
        payload: IntentJourneyTransition,
        actor_id: UUID,
    ) -> CustomerIntentJourney:
        if payload.status == entity.status:
            raise IntelligenceScopeError("Intent journey must transition to a different stage.")
        self._evidence(payload.evidence_references, entity.organization_id, entity.customer_id)
        entity.status = payload.status
        entity.evidence_references = [
            item.model_dump(mode="json") for item in payload.evidence_references
        ]
        entity.confidence = payload.confidence
        return self._save(entity, actor_id, "intelligence.intent_journey.transitioned")

    def create_sales_signal(self, payload: SalesIntentCreate, actor_id: UUID) -> SalesIntentSignal:
        self._customer(payload.customer_id, payload.organization_id)
        self._evidence(payload.evidence_references, payload.organization_id, payload.customer_id)
        return self._save(
            SalesIntentSignal(
                organization_id=payload.organization_id,
                customer_id=payload.customer_id,
                evidence_references=[
                    item.model_dump(mode="json") for item in payload.evidence_references
                ],
                intent_type=payload.intent_type,
                confidence=payload.confidence,
                recommendation=payload.recommendation,
            ),
            actor_id,
            "intelligence.sales_intent_signal.created",
        )

    def create_support_learning(
        self, payload: SupportLearningCreate, actor_id: UUID
    ) -> SupportLearningSignal:
        issue = self._row(
            "support_case_intelligence", payload.source_issue_id, payload.organization_id
        )
        return self._save(
            SupportLearningSignal(
                **payload.model_dump(exclude={"customer_impact"}),
                customer_impact=payload.customer_impact or issue["customer_impact"],
            ),
            actor_id,
            "intelligence.support_learning.created",
        )

    def dashboard(self, organization_id: UUID) -> JourneyDashboardRead:
        event_table = Base.metadata.tables["customer_journey_events"]
        engagement = self._counts(event_table, event_table.c.event_type, organization_id)
        intent_distribution = self._counts(
            CustomerIntentJourney.__table__,
            CustomerIntentJourney.__table__.c.status,
            organization_id,
        )
        sales = self._counts(
            SalesIntentSignal.__table__, SalesIntentSignal.__table__.c.intent_type, organization_id
        )
        support = self._counts(
            SupportLearningSignal.__table__,
            SupportLearningSignal.__table__.c.root_cause_category,
            organization_id,
        )
        return JourneyDashboardRead(
            organization_id=organization_id,
            customer_engagement=engagement,
            intent_distribution=intent_distribution,
            sales_signals=sales,
            support_trends=support,
        )

    def scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or cast(Any, entity).organization_id != organization_id:
            raise IntelligenceScopeError("Intelligence record was not found in this organization.")
        return entity

    def _evidence(self, references: list[Any], organization_id: UUID, customer_id: UUID) -> None:
        table_names = {
            "journey_event": "customer_journey_events",
            "conversation_intent": "conversation_intents",
            "customer_signal": "customer_signals",
        }
        for reference in references:
            row = self._row(
                table_names[reference.reference_type], reference.reference_id, organization_id
            )
            if reference.reference_type == "journey_event" and row["customer_id"] != customer_id:
                raise IntelligenceScopeError("Journey evidence belongs to another customer.")
            if reference.reference_type == "conversation_intent":
                message = self._row("conversation_messages", row["message_id"], organization_id)
                thread = self._row("conversation_threads", message["thread_id"], organization_id)
                if thread["customer_id"] != customer_id:
                    raise IntelligenceScopeError(
                        "Conversation evidence belongs to another customer."
                    )

    def _row(self, table_name: str, entity_id: UUID, organization_id: UUID) -> Any:
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
            raise IntelligenceScopeError("Evidence was not found in this organization.")
        return row

    def _customer(self, customer_id: UUID, organization_id: UUID) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name="customers",
            reference_id=customer_id,
            organization_id=organization_id,
        ):
            raise IntelligenceScopeError("Customer was not found in this organization.")

    def _counts(self, table: Any, column: Any, organization_id: UUID) -> dict[str, int]:
        rows = self.session.execute(
            select(column, func.count())
            .where(table.c.organization_id == organization_id)
            .group_by(column)
        )
        return dict(Counter({str(key): int(value) for key, value in rows}))

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        audited = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=audited.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=audited.__tablename__,
            entity_id=audited.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
