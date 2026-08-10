import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.opportunity_models import (
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    ProductCandidate,
)
from commerce_os.intelligence.opportunity_schemas import (
    OpportunityRiskCreate,
    OpportunityScoreCreate,
)
from commerce_os.intelligence.opportunity_services import (
    OpportunityRiskService,
    OpportunityScoringService,
)
from sqlalchemy.orm import Session


def opportunity_context(session: Session):  # type: ignore[no-untyped-def]
    organization = Organization(name="Opportunity Org", slug="opportunity-org")
    session.add(organization)
    session.flush()
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="European heat wave cooling demand",
        description="Time-bounded demand observation.",
        category="Cooling",
        market="Consumer climate products",
        geography="Europe",
        trigger_type="weather_event",
        timing_window="Next 30 days",
        status="observed",
        confidence_score=0.8,
    )
    session.add(opportunity)
    session.commit()
    return organization, opportunity


def test_opportunity_entities_are_distinct_models() -> None:
    assert MarketOpportunity.__tablename__ == "market_opportunities"
    assert OpportunityEvidence.__tablename__ == "opportunity_evidence"
    assert ProductCandidate.__tablename__ == "product_candidates"
    assert OpportunityScore.__tablename__ == "opportunity_scores"
    assert OpportunityRisk.__tablename__ == "opportunity_risks"


def test_deterministic_scoring_uses_frozen_v1_formula(db_session: Session) -> None:
    organization, opportunity = opportunity_context(db_session)
    payload = OpportunityScoreCreate(
        organization_id=organization.id,
        opportunity_id=opportunity.id,
        demand_score=80,
        pain_score=70,
        trend_score=90,
        margin_score=60,
        competition_score=40,
        ip_risk_score=20,
        dispute_risk_score=10,
    )
    service = OpportunityScoringService(db_session)
    assert service.calculate(payload) == 74.75
    score = service.score(payload)
    assert score.overall_score == 74.75
    assert score.formula_version == "v1.0"
    payload.demand_score = 100
    updated = service.score(payload)
    assert updated.id == score.id
    assert updated.overall_score == 79.75


def test_risk_service_models_supported_risk_and_rejects_cross_scope(
    db_session: Session,
) -> None:
    organization, opportunity = opportunity_context(db_session)
    risk = OpportunityRiskService(db_session).create(
        OpportunityRiskCreate(
            organization_id=organization.id,
            opportunity_id=opportunity.id,
            risk_type="trademark",
            severity="high",
            description="Candidate wording requires a trademark review.",
        )
    )
    assert risk.risk_type == "trademark"
    assert risk.status == "open"
    other = Organization(name="Other Opportunity Org", slug="other-opportunity-org")
    db_session.add(other)
    db_session.commit()
    with pytest.raises(IntelligenceScopeError):
        OpportunityRiskService(db_session).create(
            OpportunityRiskCreate(
                organization_id=other.id,
                opportunity_id=opportunity.id,
                risk_type="payment",
                severity="medium",
                description="Cross-scope attempt.",
            )
        )
