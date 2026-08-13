from datetime import UTC, datetime, timedelta

from commerce_os.finance.models import RevenueObservation
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.operations.conversation_models import ConversationThread, ThreadStatus
from commerce_os.operations.models import Customer
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str) -> tuple[Organization, Customer]:
    organization = Organization(name=f"Customer 360 {slug}", slug=f"customer-360-{slug}")
    session.add(organization)
    session.flush()
    customer = Customer(
        organization_id=organization.id,
        display_name=f"Customer {slug}",
        status="active",
        attributes={"source": "operations"},
    )
    session.add(customer)
    session.commit()
    return organization, customer


def test_identity_journey_projection_and_value_are_advisory(
    client: TestClient, db_session: Session
) -> None:
    organization, customer = foundation(db_session, "workflow")
    thread = ConversationThread(
        organization_id=organization.id,
        customer_id=customer.id,
        channel="website",
        status=ThreadStatus.OPEN,
        priority="normal",
    )
    db_session.add(thread)
    db_session.commit()
    base = {"organization_id": str(organization.id), "customer_id": str(customer.id)}
    identity = client.post(
        "/api/v1/customer-identity-links",
        json=base
        | {
            "identity_type": "email",
            "external_reference": "customer@example.invalid",
            "source": "manual://observation",
            "confidence": 0.8,
        },
    )
    assert identity.status_code == 201
    now = datetime.now(UTC)
    for index, event_type in enumerate(("content_viewed", "support_request")):
        response = client.post(
            "/api/v1/customer-journey-events",
            json=base
            | {
                "identity_link_id": identity.json()["id"],
                "event_type": event_type,
                "source": "manual://observation",
                "reference_id": f"event-{index}",
                "metadata": {"observed": True},
                "occurred_at": (now + timedelta(seconds=index)).isoformat(),
            },
        )
        assert response.status_code == 201
    value = client.post(
        "/api/v1/customer-value-assessments",
        json=base
        | {
            "revenue_indicator": 80,
            "margin_indicator": 60,
            "repeat_probability": 0.4,
            "strategic_potential": 50,
            "risk_indicator": 20,
        },
    )
    assert value.status_code == 201
    assert value.json()["score"] == 45.0
    finance_before = db_session.scalar(select(func.count()).select_from(RevenueObservation))
    approvals_before = db_session.scalar(select(func.count()).select_from(ApprovalRequest))
    profile = client.get(
        f"/api/v1/customer-360/{customer.id}", params={"organization_id": organization.id}
    )
    assert profile.status_code == 200
    assert profile.json()["identity_count"] == 1
    assert profile.json()["conversation_count"] == 1
    assert profile.json()["journey_summary"]["event_count"] == 2
    assert profile.json()["risk_summary"]["risk_event_count"] == 1
    assert profile.json()["value_summary"]["score"] == 45.0
    db_session.refresh(customer)
    db_session.refresh(thread)
    assert customer.attributes == {"source": "operations"}
    assert thread.status == ThreadStatus.OPEN
    assert db_session.scalar(select(func.count()).select_from(RevenueObservation)) == finance_before
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == approvals_before
    assert client.post("/api/v1/customer-360", json=base).status_code == 405
    assert client.post("/api/v1/customer-360/execute", json=base).status_code in {404, 405, 422}


def test_customer_360_tenant_isolation_and_identity_ownership(
    client: TestClient, db_session: Session
) -> None:
    owner, customer = foundation(db_session, "owner")
    other, _ = foundation(db_session, "other")
    cross_identity = client.post(
        "/api/v1/customer-identity-links",
        json={
            "organization_id": str(other.id),
            "customer_id": str(customer.id),
            "identity_type": "social",
            "external_reference": "external-1",
            "source": "manual://observation",
            "confidence": 0.5,
        },
    )
    assert cross_identity.status_code == 404
    cross_profile = client.get(
        f"/api/v1/customer-360/{customer.id}", params={"organization_id": str(other.id)}
    )
    assert cross_profile.status_code == 403
    owner_list = client.get(
        "/api/v1/customer-identity-links", params={"organization_id": str(owner.id)}
    )
    assert owner_list.status_code == 200 and owner_list.json() == []
