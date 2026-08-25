from commerce_os.shared.outbox import OutboxEvent, OutboxStatus
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_revenue_experiment_operations import operations_foundation


def test_operational_readiness_is_authenticated_tenant_scoped_and_secret_safe(
    client: TestClient, db_session: Session
) -> None:
    entities, *_ = operations_foundation(db_session, "operability")
    response = client.get(
        "/api/v1/growth-operational-readiness",
        params={"organization_id": str(entities[0].id)},
        headers={"X-Actor-ID": str(entities[1].id)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["organization_id"] == str(entities[0].id)
    assert payload["database"] == "ready"
    assert payload["manual_send_mode"] == "active"
    assert payload["external_connectors"] == "not_configured"
    assert "token" not in str(payload).lower()
    assert "password" not in str(payload).lower()


def test_operational_readiness_counts_only_growth_research_for_tenant(
    client: TestClient, db_session: Session
) -> None:
    entities, *_ = operations_foundation(db_session, "operability-count")
    other, *_ = operations_foundation(db_session, "operability-other")
    for index, organization in enumerate((entities[0], other[0])):
        db_session.add(
            OutboxEvent(
                event_id=organization.id,
                event_type="growth.business_research_requested",
                occurred_at=entities[0].created_at,
                actor={"actor_type": "human", "actor_id": str(entities[1].id)},
                source="test",
                idempotency_key=f"operability-{index}",
                correlation_id=organization.id,
                organization_id=organization.id,
                schema_version=1,
                payload={},
                status=OutboxStatus.PENDING,
            )
        )
    db_session.commit()
    response = client.get(
        "/api/v1/growth-operational-readiness",
        params={"organization_id": str(entities[0].id)},
        headers={"X-Actor-ID": str(entities[1].id)},
    )
    assert response.status_code == 200
    assert response.json()["queued_research"] == 1
