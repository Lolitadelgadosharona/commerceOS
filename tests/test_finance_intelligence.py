from datetime import date
from decimal import Decimal

import pytest
from commerce_os.build.models import Product
from commerce_os.finance.errors import FinanceError
from commerce_os.finance.schemas import (
    ContributionProfitCreate,
    CostObservationCreate,
    FinancialPeriodCreate,
    RevenueObservationCreate,
    UnitEconomicsCreate,
)
from commerce_os.finance.services import FinanceIntelligenceService
from commerce_os.governance.models import Organization, Project
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Finance Test {slug}", slug=slug)
    session.add(organization)
    session.flush()
    project = Project(
        organization_id=organization.id, name="Finance Project", slug=f"{slug}-project"
    )
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"{slug}-brand")
    session.add_all([project, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Care product",
        category="Care",
        status="approved",
    )
    session.add(product)
    session.commit()
    return organization, project, product


def test_profit_cost_categories_unit_economics_and_tenant_isolation(db_session: Session) -> None:
    organization, project, product = foundation(db_session, "finance")
    other, _, _ = foundation(db_session, "finance-other")
    service = FinanceIntelligenceService(db_session)
    period = service.create_period(
        FinancialPeriodCreate(
            organization_id=organization.id,
            period_type="monthly",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
        )
    )
    service.create_revenue(
        RevenueObservationCreate(
            organization_id=organization.id,
            project_id=project.id,
            product_id=product.id,
            channel="website",
            amount=Decimal("1000"),
            currency="USD",
            source_type="manual",
            observation_date=date(2026, 8, 10),
        )
    )
    costs = {
        "product_cost": "300",
        "shipping_cost": "100",
        "ad_cost": "100",
        "refund_cost": "50",
        "dispute_cost": "25",
        "operation_cost": "25",
        "platform_fee": "50",
        "creative_cost": "50",
    }
    for category, amount in costs.items():
        service.create_cost(
            CostObservationCreate(
                organization_id=organization.id,
                product_id=product.id,
                channel="website",
                category=category,
                amount=Decimal(amount),
                currency="USD",
                observation_date=date(2026, 8, 10),
            )
        )
    assessment = service.assess_contribution(
        ContributionProfitCreate(
            organization_id=organization.id,
            product_id=product.id,
            period_id=period.id,
            currency="USD",
            confidence=0.95,
        )
    )
    assert assessment.revenue == Decimal("1000")
    assert assessment.cost == Decimal("600")
    assert assessment.contribution_profit == Decimal("400")
    assert assessment.margin_percentage == 40
    assert "platform_fee" not in assessment.component_snapshot
    unit = service.assess_unit_economics(
        UnitEconomicsCreate(
            organization_id=organization.id,
            product_id=product.id,
            average_order_value=Decimal("100"),
            customer_acquisition_cost=Decimal("30"),
            gross_margin=0.6,
            refund_rate=0.1,
            dispute_rate=0.05,
            lifetime_value_estimate=Decimal("200"),
        )
    )
    assert unit.profitability_score == 82.5
    with pytest.raises(FinanceError):
        service.assess_contribution(
            ContributionProfitCreate(
                organization_id=other.id,
                product_id=product.id,
                period_id=period.id,
                currency="USD",
                confidence=1,
            )
        )


def test_finance_api_insights_risk_and_authority_boundaries(
    client: TestClient, db_session: Session
) -> None:
    organization, project, product = foundation(db_session, "finance-api")
    base = {"organization_id": str(organization.id)}
    period = client.post(
        "/api/v1/financial-periods",
        json=base
        | {
            "period_type": "monthly",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        },
    )
    assert period.status_code == 201
    period_id = period.json()["id"]
    assert (
        client.post(
            "/api/v1/revenue-observations",
            json=base
            | {
                "project_id": str(project.id),
                "product_id": str(product.id),
                "channel": "website",
                "amount": "250.00",
                "currency": "USD",
                "source_type": "manual",
                "observation_date": "2026-08-05",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/cost-observations",
            json=base
            | {
                "product_id": str(product.id),
                "channel": "website",
                "category": "product_cost",
                "amount": "100.00",
                "currency": "USD",
                "observation_date": "2026-08-05",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/contribution-profit",
            json=base
            | {
                "product_id": str(product.id),
                "period_id": period_id,
                "currency": "USD",
                "confidence": 1,
            },
        ).json()["contribution_profit"]
        == "150.00"
    )
    assert (
        client.post(
            "/api/v1/unit-economics",
            json=base
            | {
                "product_id": str(product.id),
                "average_order_value": "100",
                "customer_acquisition_cost": "25",
                "gross_margin": 0.55,
                "refund_rate": 0.05,
                "dispute_rate": 0.01,
                "lifetime_value_estimate": "180",
            },
        ).status_code
        == 201
    )
    insight = client.post(
        "/api/v1/cfo-insights",
        json=base
        | {
            "type": "margin_risk",
            "severity": "medium",
            "finding": "Observed margin compression.",
            "impact": "Reduced contribution profit.",
            "recommendation": "Decision review; no automatic action.",
            "confidence": 0.8,
        },
    )
    assert insight.status_code == 201
    risk = client.post(
        "/api/v1/financial-risk-signals",
        json=base
        | {
            "period_id": period_id,
            "product_id": str(product.id),
            "risk_type": "margin_compression",
            "severity": "medium",
            "evidence_reference": f"financial-period:{period_id}",
        },
    )
    assert risk.status_code == 201
    assert client.post("/api/v1/payments", json={}).status_code == 404
    assert client.post("/api/v1/refunds", json={}).status_code == 404
    for endpoint in (
        "financial-periods",
        "revenue-observations",
        "cost-observations",
        "contribution-profit",
        "unit-economics",
        "cfo-insights",
        "financial-risk-signals",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
