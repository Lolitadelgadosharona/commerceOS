from datetime import date

from commerce_os.finance.models import RevenueObservation
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.operations.models import Customer, SalesOpportunity
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str) -> tuple[Organization, Customer]:
    organization = Organization(name=f"Strategic {slug}", slug=f"strategic-{slug}")
    session.add(organization)
    session.flush()
    customer = Customer(
        organization_id=organization.id,
        display_name=f"Customer {slug}",
        status="active",
        attributes={"owner": "operations"},
    )
    session.add(customer)
    session.commit()
    return organization, customer


def create_account(
    client: TestClient, organization: Organization, customer: Customer
) -> dict[str, object]:
    response = client.post(
        "/api/v1/strategic-accounts",
        json={
            "organization_id": str(organization.id),
            "customer_id": str(customer.id),
            "relationship_stage": "developing",
            "relationship_strength": 70,
            "commercial_potential": 80,
            "expansion_potential": 75,
            "replenishment_potential": 60,
            "risk_level": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_strategic_account_advisory_workflow(client: TestClient, db_session: Session) -> None:
    organization, customer = foundation(db_session, "workflow")
    account = create_account(client, organization, customer)
    base = {"organization_id": str(organization.id), "strategic_account_id": account["id"]}
    stakeholder = client.post(
        "/api/v1/account-stakeholders",
        json=base
        | {
            "contact_reference": "supplied:contact-1",
            "role": "buyer",
            "decision_influence": 80,
            "decision_maker": True,
            "relationship_strength": 65,
            "evidence_reference": "conversation:1",
        },
    )
    assert stakeholder.status_code == 201
    missing = client.post("/api/v1/replenishment-assessments", json=base | {"confidence": 0.3})
    assert missing.status_code == 201 and missing.json()["replenishment_probability"] is None
    replenishment = client.post(
        "/api/v1/replenishment-assessments",
        json=base
        | {
            "historical_purchase_references": ["supplied:purchase-1"],
            "purchase_frequency_indicator": 80,
            "last_purchase_date": date(2026, 8, 1).isoformat(),
            "expected_replenishment_cycle_days": 30,
            "confidence": 0.75,
            "evidence_summary": "Supplied purchase reference",
        },
    )
    assert replenishment.status_code == 201
    assert replenishment.json()["replenishment_probability"] == 0.6
    assert replenishment.json()["estimated_next_purchase_start"] == "2026-08-31"
    sales_before = db_session.scalar(select(func.count()).select_from(SalesOpportunity))
    expansion = client.post(
        "/api/v1/customer-expansion-opportunities",
        json=base
        | {
            "opportunity_type": "cross_sell",
            "estimated_value_indicator": 70,
            "confidence": 0.8,
            "evidence": {"source": "conversation:1"},
            "risk_indicator": 20,
        },
    )
    assert expansion.status_code == 201
    assert (
        client.patch(
            f"/api/v1/customer-expansion-opportunities/{expansion.json()['id']}",
            params={"organization_id": organization.id},
            json={"status": "review"},
        ).status_code
        == 200
    )
    assert db_session.scalar(select(func.count()).select_from(SalesOpportunity)) == sales_before
    finance_before = db_session.scalar(select(func.count()).select_from(RevenueObservation))
    approval_before = db_session.scalar(select(func.count()).select_from(ApprovalRequest))
    action = client.post(
        "/api/v1/customer-next-best-actions",
        json=base
        | {
            "customer_id": str(customer.id),
            "recommendation_type": "risk_review",
            "reason": "Material supplied risk evidence",
            "evidence_references": ["risk:1"],
            "priority": "high",
            "confidence": 0.9,
            "human_review_required": True,
        },
    )
    assert action.status_code == 201 and action.json()["decision_queue_item_id"]
    assert db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    no_action = client.post(
        "/api/v1/customer-next-best-actions",
        json=base
        | {
            "customer_id": str(customer.id),
            "recommendation_type": "no_action",
            "reason": "Insufficient evidence",
            "priority": "high",
            "confidence": 0.4,
            "human_review_required": True,
        },
    )
    assert no_action.status_code == 201 and no_action.json()["decision_queue_item_id"] is None
    assert db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    assert db_session.scalar(select(func.count()).select_from(RevenueObservation)) == finance_before
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == approval_before
    db_session.refresh(customer)
    assert customer.attributes == {"owner": "operations"}


def test_score_determinism_risk_and_tenant_boundaries(
    client: TestClient, db_session: Session
) -> None:
    owner, customer = foundation(db_session, "owner")
    other, _ = foundation(db_session, "other")
    account = create_account(client, owner, customer)
    base = {"organization_id": str(owner.id), "strategic_account_id": account["id"]}
    inputs = {"relationship_strength": 80, "strategic_importance": 70, "expansion_potential": 60}
    first = client.post("/api/v1/strategic-account-scores", json=base | {"input_values": inputs})
    second = client.post("/api/v1/strategic-account-scores", json=base | {"input_values": inputs})
    assert first.status_code == 201 and first.json()["score"] == second.json()["score"]
    assert first.json()["evidence_coverage"] < 1
    risky = client.post(
        "/api/v1/strategic-account-scores",
        json=base
        | {
            "input_values": inputs
            | {
                "payment_risk": 100,
                "refund_risk": 100,
                "dispute_risk": 100,
                "operational_burden": 100,
            }
        },
    )
    assert risky.json()["score"] < first.json()["score"]
    cross = client.post(
        "/api/v1/account-stakeholders",
        json={
            "organization_id": str(other.id),
            "strategic_account_id": account["id"],
            "contact_reference": "bad",
            "role": "buyer",
            "decision_influence": 50,
            "relationship_strength": 50,
        },
    )
    assert cross.status_code == 404
    assert client.post("/api/v1/strategic-accounts/execute", json={}).status_code in {404, 405, 422}
    profile = client.get(
        f"/api/v1/customer-360/{customer.id}", params={"organization_id": owner.id}
    )
    assert profile.status_code == 200
    assert client.post("/api/v1/customer-360", json={}).status_code == 405
    dashboard = client.get(
        "/api/v1/dashboard/customer-health", params={"organization_id": owner.id}
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["strategic_account_indicators"]["strategic_accounts"] == 1
