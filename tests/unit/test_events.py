from datetime import datetime
from uuid import uuid4

import pytest
from commerce_os.shared.events import BusinessEventEnvelope, EventActor
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus, add_to_outbox
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session


def build_event() -> BusinessEventEnvelope:
    return BusinessEventEnvelope(
        event_type="customer.identity_observed",
        actor=EventActor(actor_type="service", actor_id="identity-test"),
        source="unit_test",
        idempotency_key="identity-observed-1",
        correlation_id=uuid4(),
        organization_id=uuid4(),
        payload={"observation": "redacted"},
    )


def test_event_round_trip_serialization() -> None:
    event = build_event()
    restored = BusinessEventEnvelope.model_validate_json(event.model_dump_json())
    assert restored == event


def test_event_rejects_naive_timestamp() -> None:
    data = build_event().model_dump()
    data["occurred_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        BusinessEventEnvelope.model_validate(data)


def test_outbox_persists_envelope_in_same_session(db_session: Session) -> None:
    event = build_event()
    record = add_to_outbox(db_session, event)
    db_session.commit()

    stored = db_session.scalar(select(OutboxEvent).where(OutboxEvent.id == record.id))
    assert stored is not None
    assert stored.event_id == event.event_id
    assert stored.status == OutboxStatus.PENDING
    assert stored.payload == {"observation": "redacted"}
