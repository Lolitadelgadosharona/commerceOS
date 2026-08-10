from decimal import Decimal

from commerce_os.governance.models import Organization
from commerce_os.intelligence.opportunity_models import MarketOpportunity, OpportunityScore
from commerce_os.intelligence.product_models import ProductHypothesis
from commerce_os.intelligence.product_schemas import (
    ProductEconomicsCreate,
    ProductInvestmentScoreCreate,
    ProductRiskCreate,
)
from commerce_os.intelligence.product_services import (
    ProductEconomicsService,
    ProductInvestmentScoringService,
    ProductRiskService,
)
from sqlalchemy.orm import Session


def foundation(db_session: Session) -> tuple[Organization, ProductHypothesis]:
    organization = Organization(name="Product Test", slug="product-test")
    db_session.add(organization)
    db_session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Cooling demand",
        description="Heat-driven demand",
        category="Cooling",
        market="Consumers",
        geography="Europe",
        trigger_type="weather_event",
        timing_window="Summer",
        status="qualified",
        confidence_score=0.8,
    )
    db_session.add(opportunity)
    db_session.flush()
    db_session.add(
        OpportunityScore(
            organization_id=organization.id,
            opportunity_id=opportunity.id,
            demand_score=80,
            pain_score=80,
            trend_score=80,
            margin_score=80,
            competition_score=50,
            ip_risk_score=20,
            dispute_risk_score=20,
            overall_score=80,
            formula_version="v1.0",
        )
    )
    product = ProductHypothesis(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        name="Portable cooler",
        description="Hypothesis",
        customer_problem="Excess heat",
        solution_description="Portable cooling",
        target_customer="Urban renters",
        target_market="Europe",
        status="evaluating",
        confidence_score=0.8,
    )
    db_session.add(product)
    db_session.commit()
    return organization, product


def test_economics_and_investment_calculations(db_session: Session) -> None:
    organization, product = foundation(db_session)
    economics = ProductEconomicsService(db_session).upsert(
        ProductEconomicsCreate(
            organization_id=organization.id,
            product_id=product.id,
            selling_price=Decimal("100.00"),
            estimated_product_cost=Decimal("30.00"),
            estimated_shipping_cost=Decimal("10.00"),
            payment_cost=Decimal("3.00"),
            estimated_marketing_cost=Decimal("20.00"),
            currency="usd",
        )
    )
    assert economics.contribution_margin == Decimal("37.00")
    assert economics.margin_percentage == Decimal("37.0000")
    assert economics.currency == "USD"
    ProductRiskService(db_session).create(
        ProductRiskCreate(
            organization_id=organization.id,
            product_id=product.id,
            risk_type="quality",
            severity="high",
            description="Requires verification",
        )
    )
    score = ProductInvestmentScoringService(db_session).score(
        ProductInvestmentScoreCreate(
            organization_id=organization.id, product_id=product.id, competition_score=40
        )
    )
    assert score.risk_score == 75
    assert score.overall_score == 58
    assert score.formula_version == "v1.0"


def test_product_tables_are_registered() -> None:
    assert ProductHypothesis.__tablename__ == "product_hypotheses"
