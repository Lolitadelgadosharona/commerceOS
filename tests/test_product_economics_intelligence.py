from decimal import Decimal

import pytest
from commerce_os.finance.models import CostObservation, RevenueObservation
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.intelligence.commercial_risk_models import ProductRiskAssessment
from commerce_os.intelligence.economics_schemas import ProductProfitAssessmentCreate
from commerce_os.intelligence.economics_services import ProductEconomicsIntelligenceService
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.opportunity_models import MarketOpportunity, ProductCandidate
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def candidate_foundation(session: Session, slug: str) -> tuple[Organization, ProductCandidate]:
    organization = Organization(name=f"Economics {slug}", slug=f"economics-{slug}")
    session.add(organization)
    session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Economics opportunity",
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
        product_name="Economics candidate",
        category="home",
        customer_need="Affordable solution",
        estimated_margin=0.4,
        risk_level="low",
        status="reviewing",
    )
    session.add(candidate)
    session.commit()
    return organization, candidate


def test_decimal_profit_scenarios_and_risk_adjusted_advice(
    client: TestClient, db_session: Session
) -> None:
    organization, candidate = candidate_foundation(db_session, "api")
    base = {
        "organization_id": str(organization.id),
        "product_candidate_id": str(candidate.id),
    }
    profile = client.post(
        "/api/v1/product-economic-profiles",
        json=base
        | {
            "product_cost": "20.1234",
            "shipping_cost": "5.4321",
            "packaging_cost": "1.1111",
            "transaction_cost": "1.2222",
            "estimated_acquisition_cost": "10.5555",
            "refund_rate_assumption": "0.050000",
            "dispute_rate_assumption": "0.010000",
            "currency": "usd",
            "confidence": "0.800000",
        },
    )
    assert profile.status_code == 201
    assert profile.json()["currency"] == "USD"
    assessed = client.post(
        "/api/v1/product-profit-assessments",
        json=base | {"selling_price": "80.9999"},
    )
    assert assessed.status_code == 201
    assert Decimal(assessed.json()["gross_margin"]) == Decimal("53.1111")
    assert Decimal(assessed.json()["contribution_profit"]) == Decimal("37.6956")
    assert Decimal(assessed.json()["margin_score"]) == Decimal("46.5378")
    scenario_profits: dict[str, Decimal] = {}
    for scenario in ("conservative", "base", "optimistic"):
        response = client.post("/api/v1/profit-scenarios", json=base | {"scenario": scenario})
        assert response.status_code == 201
        scenario_profits[scenario] = Decimal(response.json()["profit"])
    assert (
        scenario_profits["conservative"] < scenario_profits["base"] < scenario_profits["optimistic"]
    )
    db_session.add(
        ProductRiskAssessment(
            organization_id=organization.id,
            product_candidate_id=candidate.id,
            risk_score=20,
            risk_level="low",
            formula_version="product-commercial-risk-v1",
            assessment_inputs={"signal_ids": ["internal-test"]},
            confidence=0.8,
        )
    )
    db_session.commit()
    final = client.post(
        "/api/v1/risk-adjusted-profit-assessments",
        json=base | {"opportunity_score": "80.0000"},
    )
    assert final.status_code == 201
    assert Decimal(final.json()["final_score"]) == Decimal("69.9613")
    assert final.json()["recommendation"] == "test"
    assert db_session.scalar(select(func.count()).select_from(RevenueObservation)) == 0
    assert db_session.scalar(select(func.count()).select_from(CostObservation)) == 0
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    for endpoint in (
        "product-economic-profiles",
        "product-profit-assessments",
        "profit-scenarios",
        "risk-adjusted-profit-assessments",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200
        assert response.json()


def test_formula_boundaries_tenant_isolation_and_no_execution(
    client: TestClient, db_session: Session
) -> None:
    owner, candidate = candidate_foundation(db_session, "owner")
    other, _ = candidate_foundation(db_session, "other")
    base = {
        "organization_id": str(owner.id),
        "product_candidate_id": str(candidate.id),
    }
    invalid = client.post(
        "/api/v1/product-economic-profiles",
        json=base
        | {
            "product_cost": "1.0000",
            "shipping_cost": "1.0000",
            "packaging_cost": "1.0000",
            "transaction_cost": "1.0000",
            "estimated_acquisition_cost": "1.0000",
            "refund_rate_assumption": "1.000001",
            "dispute_rate_assumption": "0.000000",
            "currency": "USD",
            "confidence": "0.500000",
        },
    )
    assert invalid.status_code == 422
    assert (
        client.post(
            "/api/v1/product-profit-assessments",
            json=base | {"selling_price": "0.0000"},
        ).status_code
        == 422
    )
    with pytest.raises(IntelligenceScopeError):
        ProductEconomicsIntelligenceService(db_session).assess_profit(
            ProductProfitAssessmentCreate(
                organization_id=other.id,
                product_candidate_id=candidate.id,
                selling_price=Decimal("50.0000"),
            )
        )
    assert (
        ProductEconomicsIntelligenceService.recommendation(Decimal(80), Decimal(20)).value == "go"
    )
    assert (
        ProductEconomicsIntelligenceService.recommendation(Decimal(60), Decimal(50)).value == "test"
    )
    assert (
        ProductEconomicsIntelligenceService.recommendation(Decimal(50), Decimal(60)).value
        == "review"
    )
    assert (
        ProductEconomicsIntelligenceService.recommendation(Decimal(90), Decimal(80)).value
        == "reject"
    )
    assert client.post("/api/v1/risk-adjusted-profit-assessments/execute", json={}).status_code in {
        404,
        405,
        422,
    }
