import pytest
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.intelligence.commercial_risk_models import ProductRiskSignal
from commerce_os.intelligence.commercial_risk_schemas import ProductRiskAssessmentCreate
from commerce_os.intelligence.commercial_risk_services import CommercialRiskService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import MarketOpportunity, ProductCandidate
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def candidate_foundation(session: Session, slug: str) -> tuple[Organization, ProductCandidate]:
    organization = Organization(name=f"Risk {slug}", slug=f"risk-{slug}")
    session.add(organization)
    session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Controlled product opportunity",
        description="Existing opportunity",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="customer_pain",
        timing_window="90 days",
        status="evaluating",
        confidence_score=0.8,
    )
    session.add(opportunity)
    session.flush()
    candidate = ProductCandidate(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        product_name="Candidate",
        category="home",
        customer_need="Safer product",
        estimated_margin=0.4,
        risk_level="medium",
        status="reviewing",
    )
    session.add(candidate)
    session.commit()
    return organization, candidate


def test_risk_assessment_viability_and_no_automatic_approval(
    client: TestClient, db_session: Session
) -> None:
    organization, candidate = candidate_foundation(db_session, "api")
    base = {
        "organization_id": str(organization.id),
        "product_candidate_id": str(candidate.id),
    }
    first = client.post(
        "/api/v1/product-risk-signals",
        json=base
        | {
            "risk_type": "safety",
            "severity": "high",
            "evidence": {"source_reference": "internal://safety-review/1"},
            "confidence": 0.8,
        },
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/product-risk-signals",
        json=base
        | {
            "risk_type": "regulatory",
            "severity": "critical",
            "evidence": {"source_reference": "internal://compliance-review/2"},
            "confidence": 0.6,
        },
    )
    assert second.status_code == 201
    risk = client.post("/api/v1/product-risk-assessments", json=base)
    assert risk.status_code == 201
    assert risk.json()["risk_score"] == 85.71
    assert risk.json()["risk_level"] == "critical"
    assert risk.json()["assessment_inputs"]["signal_count"] == 2
    viability = client.post(
        "/api/v1/commercial-viability-assessments",
        json=base | {"opportunity_score": 90},
    )
    assert viability.status_code == 201
    assert viability.json()["adjusted_score"] == 4.29
    assert viability.json()["recommendation"] == "reject"
    assert "human decision authority" in viability.json()["reasoning"]
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    assert (
        client.post(
            "/api/v1/commercial-viability-assessments",
            json=base | {"opportunity_score": 101},
        ).status_code
        == 422
    )
    for endpoint in (
        "product-risk-signals",
        "product-risk-assessments",
        "commercial-viability-assessments",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200
        assert response.json()


def test_signal_lifecycle_tenant_isolation_and_authority_boundaries(
    client: TestClient, db_session: Session
) -> None:
    owner, candidate = candidate_foundation(db_session, "owner")
    other, _ = candidate_foundation(db_session, "other")
    signal = ProductRiskSignal(
        organization_id=owner.id,
        product_candidate_id=candidate.id,
        risk_type="quality",
        severity="medium",
        evidence={"source_reference": "internal://quality/1"},
        confidence=0.75,
        status="open",
    )
    db_session.add(signal)
    db_session.commit()
    transitioned = client.patch(
        f"/api/v1/product-risk-signals/{signal.id}",
        params={"organization_id": str(owner.id)},
        json={"status": "mitigated"},
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "mitigated"
    assert (
        client.patch(
            f"/api/v1/product-risk-signals/{signal.id}",
            params={"organization_id": str(owner.id)},
            json={"status": "accepted"},
        ).status_code
        == 409
    )
    with pytest.raises(IntelligenceScopeError):
        CommercialRiskService(db_session).assess_risk(
            ProductRiskAssessmentCreate(organization_id=other.id, product_candidate_id=candidate.id)
        )
    with pytest.raises(IntelligenceValidationError):
        CommercialRiskService(db_session).transition_signal(signal, "open")
    assert CommercialRiskService.recommendation(75, 20).value == "go"
    assert CommercialRiskService.recommendation(55, 45).value == "test"
    assert CommercialRiskService.recommendation(40, 55).value == "review"
    assert CommercialRiskService.recommendation(80, 80).value == "reject"
    assert client.post("/api/v1/commercial-viability-assessments/approve", json={}).status_code in {
        404,
        405,
        422,
    }
