import pytest
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import BusinessGrowthProfile
from commerce_os.growth.revenue_schemas import (
    BusinessGrowthProfileCreate,
    OpportunityAnalysisCreate,
    ProspectRankingCreate,
)
from commerce_os.growth.revenue_services import GrowthRevenueService
from commerce_os.intelligence.demand_bridge_models import DemandSignal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_ai_research_operationalization import foundation
from tests.test_growthos_revenue_engine import prospect_and_evidence


def test_evidence_backed_business_profile_and_growth_opportunity(db_session: Session) -> None:
    entities = foundation(db_session, "growth-v2-profile")
    organization, user, *_ = entities
    prospect, evidence = prospect_and_evidence(db_session, entities)
    service = GrowthRevenueService(db_session)
    profile = service.create_business_profile(
        BusinessGrowthProfileCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            business_identity={"name": prospect.business_name, "website": prospect.website or ""},
            evidence_references=[evidence.id],
            digital_presence={"website": "observed", "instagram": "unknown"},
            customer_signals=["Booking path is hard to locate"],
            strengths=["Clear service category"],
            weaknesses=["Conversion path friction"],
            growth_opportunities=["website_conversion"],
            confidence=0.82,
        ),
        user.id,
    )
    opportunity = service.create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_type="website_conversion",
            problem_statement="Booking friction may suppress conversion.",
            evidence_reference=[evidence.id],
            customer_impact="Interested visitors may abandon.",
            purchase_probability=0.64,
            confidence=0.8,
            recommended_offer="Evidence-backed booking path preview",
            missing_information=["conversion analytics"],
        ),
        user.id,
    )
    assert profile.evidence_references == [str(evidence.id)]
    assert opportunity.purchase_probability == 0.64


def test_revenue_ranking_preserves_unknown_inputs(db_session: Session) -> None:
    entities = foundation(db_session, "growth-v2-ranking")
    organization, user, *_ = entities
    prospect, _ = prospect_and_evidence(db_session, entities)
    service = GrowthRevenueService(db_session)
    incomplete = service.rank_prospect(
        ProspectRankingCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            pain_severity=80,
            business_impact=75,
            accessibility=None,
            buying_signals=None,
            solution_fit=85,
        ),
        user.id,
    )
    assert incomplete.score is None
    assert incomplete.missing_inputs == ["accessibility", "buying_signals"]
    complete = service.rank_prospect(
        ProspectRankingCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            pain_severity=80,
            business_impact=75,
            accessibility=70,
            buying_signals=60,
            solution_fit=85,
        ),
        user.id,
    )
    assert complete.score == 74


def test_growth_and_commerce_demand_sources_remain_independent(db_session: Session) -> None:
    entities = foundation(db_session, "growth-v2-independence")
    organization, *_ = entities
    for source_type, source_domain in [
        ("growthos_conversation", "growth"),
        ("reddit", "intelligence"),
    ]:
        db_session.add(
            DemandSignal(
                organization_id=organization.id,
                source_domain=source_domain,
                source_reference_id=organization.id,
                source_type=source_type,
                source_reference=f"{source_type}:evidence",
                collection_method="controlled_test",
                evidence_origin="sourced_observation",
                confidence_basis="Supplied test evidence.",
                customer_segment="business owners",
                category="growth",
                problem_statement="Observed demand signal.",
                customer_language="Customer wording.",
                frequency=1,
                confidence=0.8,
                evidence_count=1,
                status="review",
            )
        )
    db_session.commit()
    dashboard = GrowthRevenueService(db_session).v2_dashboard(organization.id)
    assert dashboard.growth_demand_signals == 1
    assert dashboard.commerce_independent_demand_signals == 1


def test_profile_tenant_boundary(db_session: Session) -> None:
    entities = foundation(db_session, "growth-v2-safety")
    other = foundation(db_session, "growth-v2-other")
    organization, user, *_ = entities
    prospect, evidence = prospect_and_evidence(db_session, entities)
    with pytest.raises(GrowthError, match="this organization"):
        GrowthRevenueService(db_session).create_business_profile(
            BusinessGrowthProfileCreate(
                organization_id=organization.id,
                prospect_id=prospect.id,
                business_identity={"name": "unsafe"},
                evidence_references=[evidence.id],
                digital_presence={},
                confidence=0.5,
            ).model_copy(update={"organization_id": other[0].id}),
            user.id,
        )


def test_growth_v2_authenticated_api(db_session: Session, client: TestClient) -> None:
    entities = foundation(db_session, "growth-v2-api")
    organization, user, *_ = entities
    prospect, evidence = prospect_and_evidence(db_session, entities)
    response = client.post(
        "/api/v1/business-growth-profiles",
        json=BusinessGrowthProfileCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            business_identity={"name": prospect.business_name},
            evidence_references=[evidence.id],
            digital_presence={"website": "observed"},
            confidence=0.8,
        ).model_dump(mode="json"),
        headers={"X-Actor-ID": str(user.id)},
    )
    assert response.status_code == 201
    dashboard = client.get(
        "/api/v1/growthos-revenue-v2-dashboard",
        params={"organization_id": str(organization.id)},
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["business_profiles"] == 1
    assert db_session.query(BusinessGrowthProfile).count() == 1
