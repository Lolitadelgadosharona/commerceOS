from collections import Counter
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.intelligence.customer_360_models import Customer360Profile, CustomerJourneyEvent
from commerce_os.intelligence.customer_360_schemas import JourneyEventCreate
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization


class Customer360Service:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_event(
        self, payload: JourneyEventCreate, actor_id: UUID | None = None
    ) -> CustomerJourneyEvent:
        self._customer(payload.customer_id, payload.organization_id)
        if payload.identity_link_id is not None:
            table = Base.metadata.tables["customer_identity_links"]
            identity = self.session.execute(
                select(table.c.id).where(
                    table.c.id == payload.identity_link_id,
                    table.c.organization_id == payload.organization_id,
                    table.c.customer_id == payload.customer_id,
                )
            ).scalar_one_or_none()
            if identity is None:
                raise IntelligenceScopeError("Identity link does not match this customer.")
        values = payload.model_dump(exclude={"metadata"})
        entity = CustomerJourneyEvent(**values, event_metadata=payload.metadata)
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=payload.organization_id,
            actor_type="human" if actor_id else "system",
            actor_id=actor_id,
            action="intelligence.customer_journey_event.appended",
            entity_type="customer_journey_events",
            entity_id=entity.id,
            metadata={"result": "success", "append_only": True},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def project(self, customer_id: UUID, organization_id: UUID) -> Customer360Profile:
        self._customer(customer_id, organization_id)
        identity_table = Base.metadata.tables["customer_identity_links"]
        conversation_table = Base.metadata.tables["conversation_threads"]
        identity_count = (
            self.session.scalar(
                select(func.count())
                .select_from(identity_table)
                .where(
                    identity_table.c.organization_id == organization_id,
                    identity_table.c.customer_id == customer_id,
                )
            )
            or 0
        )
        conversation_count = (
            self.session.scalar(
                select(func.count())
                .select_from(conversation_table)
                .where(
                    conversation_table.c.organization_id == organization_id,
                    conversation_table.c.customer_id == customer_id,
                )
            )
            or 0
        )
        events = list(
            self.session.scalars(
                select(CustomerJourneyEvent)
                .where(
                    CustomerJourneyEvent.organization_id == organization_id,
                    CustomerJourneyEvent.customer_id == customer_id,
                )
                .order_by(CustomerJourneyEvent.occurred_at)
            )
        )
        event_counts = Counter(item.event_type for item in events)
        value_table = Base.metadata.tables["customer_value_assessments"]
        latest_value = (
            self.session.execute(
                select(value_table)
                .where(
                    value_table.c.organization_id == organization_id,
                    value_table.c.customer_id == customer_id,
                )
                .order_by(value_table.c.created_at.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        risk_events = event_counts["refund_reference"] + event_counts["support_request"]
        profile = self.session.scalar(
            select(Customer360Profile).where(
                Customer360Profile.organization_id == organization_id,
                Customer360Profile.customer_id == customer_id,
            )
        )
        values = {
            "identity_count": identity_count,
            "conversation_count": conversation_count,
            "journey_summary": {"event_count": len(events), "event_types": dict(event_counts)},
            "risk_summary": {"risk_event_count": risk_events},
            "value_summary": {
                "latest_assessment_id": str(latest_value["id"]),
                "score": latest_value["score"],
            }
            if latest_value
            else {"latest_assessment_id": None, "score": None},
            "last_activity_at": events[-1].occurred_at if events else None,
        }
        if profile is None:
            profile = Customer360Profile(
                organization_id=organization_id, customer_id=customer_id, **values
            )
        else:
            for key, value in values.items():
                setattr(profile, key, value)
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def _customer(self, customer_id: UUID, organization_id: UUID) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name="customers",
            reference_id=customer_id,
            organization_id=organization_id,
        ):
            raise IntelligenceScopeError("Customer was not found in this organization.")
