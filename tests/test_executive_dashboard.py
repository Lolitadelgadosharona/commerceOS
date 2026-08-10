from datetime import date

import pytest
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.decision.executive_schemas import ExecutiveMetricCreate, OperatingSignalCreate
from commerce_os.decision.executive_services import ExecutiveDecisionService
from commerce_os.finance.models import FinancialPeriod
from commerce_os.governance.models import Organization
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str) -> tuple[Organization, FinancialPeriod]:
    organization = Organization(name=f"Executive {slug}", slug=slug)
    session.add(organization)
    session.flush()
    period = FinancialPeriod(
        organization_id=organization.id,
        period_type="monthly",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        status="open",
    )
    session.add(period)
    session.commit()
    return organization, period


def test_metric_signal_lifecycle_and_tenant_isolation(db_session: Session) -> None:
    organization, period = foundation(db_session, "executive")
    other, _ = foundation(db_session, "executive-other")
    service = ExecutiveDecisionService(db_session)
    metric = service.create_metric(
        ExecutiveMetricCreate(
            organization_id=organization.id,
            metric_type="profit",
            metric_name="Contribution profit",
            value=400,
            unit="USD",
            source_domain="finance",
            period_id=period.id,
        )
    )
    assert metric.value == 400
    signal = service.create_signal(
        OperatingSignalCreate(
            organization_id=organization.id,
            domain="finance",
            severity="warning",
            title="Margin compression",
            description="Margin declined in the observed period.",
            impact="Contribution profit may decline.",
            recommendation="Review the evidence and decide; do not execute automatically.",
        )
    )
    assert service.transition_signal(signal, "acknowledged").status == "acknowledged"
    assert service.transition_signal(signal, "resolved").status == "resolved"
    with pytest.raises(DecisionScopeError):
        service.create_metric(
            ExecutiveMetricCreate(
                organization_id=other.id,
                metric_type="profit",
                metric_name="Cross-tenant metric",
                value=1,
                unit="USD",
                source_domain="finance",
                period_id=period.id,
            )
        )


def test_dashboard_queue_reviews_and_authority_boundary(
    client: TestClient, db_session: Session
) -> None:
    organization, period = foundation(db_session, "executive-api")
    base = {"organization_id": str(organization.id)}
    metric = client.post(
        "/api/v1/executive-metrics",
        json=base
        | {
            "metric_type": "revenue",
            "metric_name": "Observed revenue",
            "value": 1000,
            "unit": "USD",
            "source_domain": "finance",
            "period_id": str(period.id),
        },
    )
    assert metric.status_code == 201
    signal = client.post(
        "/api/v1/operating-signals",
        json=base
        | {
            "domain": "operations",
            "severity": "critical",
            "title": "Customer escalation",
            "description": "An observed escalation requires review.",
            "impact": "Customer trust risk.",
            "recommendation": "Review and route through existing authority.",
        },
    )
    assert signal.status_code == 201
    queue = client.post(
        "/api/v1/decision-queue",
        json=base
        | {
            "title": "Review customer escalation",
            "domain": "operations",
            "reason": "Human authority is required.",
            "priority": "critical",
            "required_action": "review",
        },
    )
    assert queue.status_code == 201
    assert queue.json()["status"] == "pending"
    assert (
        client.patch(
            f"/api/v1/decision-queue/{queue.json()['id']}",
            params=base,
            json={"status": "closed"},
        ).json()["status"]
        == "closed"
    )
    review = client.post(
        "/api/v1/operating-reviews",
        json=base
        | {
            "period_id": str(period.id),
            "summary": "Periodic evidence review.",
            "key_findings": ["Revenue observed"],
            "risks": ["Customer escalation"],
            "recommended_actions": ["Human review"],
            "confidence": 0.8,
        },
    )
    assert review.status_code == 201
    assert review.json()["status"] == "draft"
    for view in (
        "executive-overview",
        "need-your-decision",
        "financial-health",
        "product-opportunities",
        "customer-health",
        "creative-performance",
        "channel-performance",
        "risk-overview",
    ):
        response = client.get(f"/api/v1/dashboard/{view}", params=base)
        assert response.status_code == 200
        assert response.json()["organization_id"] == str(organization.id)
    assert client.post("/api/v1/dashboard/execute", json={}).status_code in {404, 405, 422}
    assert client.post("/api/v1/agent-decisions", json={}).status_code == 404
    for endpoint in (
        "executive-metrics",
        "operating-signals",
        "decision-queue",
        "operating-reviews",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
