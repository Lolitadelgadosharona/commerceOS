from uuid import uuid4

import pytest
from commerce_os.build.models import Product
from commerce_os.intelligence.demand_bridge_schemas import DemandThemeAnalysisCreate
from commerce_os.intelligence.demand_bridge_services import DemandIntelligenceService
from commerce_os.intelligence.discovery_models import OpportunityCandidateEvidence
from commerce_os.intelligence.discovery_schemas import OpportunityCandidateCreate
from commerce_os.intelligence.discovery_services import OpportunityDiscoveryService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.test_business_demand_intelligence import external_payload
from tests.test_demand_intelligence_bridge import aggregate
from tests.test_demand_intelligence_enhancement import enhanced_source


def candidate_payload(organization_id, signal_ids):  # type: ignore[no-untyped-def]
    return OpportunityCandidateCreate(
        organization_id=organization_id,
        title="Senior Pet Mobility Solutions",
        category="pet_mobility",
        customer_segment="Senior dog owners",
        customer_problem="Difficulty supporting aging pets",
        opportunity_description="Evaluate mobility support solutions backed by independent demand.",
        solution_direction="Explore safe, evidence-supported mobility aids.",
        market_context="Customer voice, marketplace, search, and seasonal evidence align.",
        demand_signal_ids=signal_ids,
        market_timing="Cold season approaching",
        risks=["product safety evidence incomplete"],
        missing_information=["supplier validation", "unit economics"],
        assumptions=["Signals represent distinct source systems."],
    )


def reviewed_signals(session: Session):  # type: ignore[no-untyped-def]
    entities, _, _, growth = aggregate(session, "opportunity-engine")
    organization, user, *_ = entities
    service = DemandIntelligenceService(session)
    signals = [growth]
    for source_type, category in [
        ("reddit", "social"),
        ("amazon_review", "marketplace"),
        ("google_trend", "search"),
    ]:
        enhanced_source(
            session,
            organization.id,
            user.id,
            source_type=source_type,
            source_category=category,
            trend_type="rising",
        )
        signals.append(
            service.ingest(
                external_payload(organization.id, source_type, f"{source_type}:senior-pets"),
                user.id,
            )
        )
    for signal in signals:
        service.transition(signal, "review", None, user.id)
    return organization, user, signals


def test_multi_source_signals_create_advisory_candidate(db_session: Session) -> None:
    products_before = db_session.scalar(select(func.count()).select_from(Product))
    organization, user, signals = reviewed_signals(db_session)
    service = OpportunityDiscoveryService(db_session)
    candidate = service.create_candidate(
        candidate_payload(organization.id, [signal.id for signal in signals]), user.id
    )
    assessment = service.candidate_assessment(candidate.id, organization.id)
    evidence = service.candidate_evidence(candidate.id, organization.id)

    assert candidate.status == "draft"
    assert candidate.confidence_score > 0
    assert assessment.demand_strength == "strong"
    assert assessment.signal_diversity == 4
    assert len(evidence) == 4
    assert db_session.scalar(select(func.count()).select_from(Product)) == products_before


def test_evidence_is_append_only_and_cross_tenant_access_fails(db_session: Session) -> None:
    organization, user, signals = reviewed_signals(db_session)
    service = OpportunityDiscoveryService(db_session)
    candidate = service.create_candidate(
        candidate_payload(organization.id, [signal.id for signal in signals[:2]]), user.id
    )
    evidence = service.candidate_evidence(candidate.id, organization.id)[0]
    evidence.contribution = "replacement"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    with pytest.raises(IntelligenceScopeError):
        service.candidate_evidence(candidate.id, uuid4())
    assert db_session.scalar(select(func.count()).select_from(OpportunityCandidateEvidence)) == 2


def test_acceptance_requires_governance_approval(db_session: Session) -> None:
    organization, user, signals = reviewed_signals(db_session)
    service = OpportunityDiscoveryService(db_session)
    candidate = service.create_candidate(
        candidate_payload(organization.id, [signal.id for signal in signals]), user.id
    )
    with pytest.raises(IntelligenceValidationError, match="approved governance"):
        service.review_candidate(candidate, "accept", None, user.id)
    rejected = service.review_candidate(candidate, "reject", None, user.id)
    assert rejected.status == "rejected"


def test_dashboard_projects_themes_and_review_queue(db_session: Session) -> None:
    organization, user, signals = reviewed_signals(db_session)
    service = OpportunityDiscoveryService(db_session)
    candidate = service.create_candidate(
        candidate_payload(organization.id, [signal.id for signal in signals[:3]]), user.id
    )
    dashboard = service.dashboard(organization.id)
    assert dashboard.opportunity_themes[0].category == "pet_mobility"
    assert dashboard.opportunity_themes[0].source_diversity == 3
    assert dashboard.review_queue[0].id == candidate.id


def test_unreviewed_or_foreign_demand_cannot_create_candidate(db_session: Session) -> None:
    organization, user, _ = reviewed_signals(db_session)
    source = enhanced_source(
        db_session,
        organization.id,
        user.id,
        source_type="news_event",
        source_category="news",
    )
    signal = DemandIntelligenceService(db_session).ingest(
        external_payload(organization.id, source.source_type, "news:unreviewed"), user.id
    )
    with pytest.raises(IntelligenceValidationError, match="human review"):
        OpportunityDiscoveryService(db_session).create_candidate(
            candidate_payload(organization.id, [signal.id]), user.id
        )
    with pytest.raises(IntelligenceScopeError):
        DemandIntelligenceService(db_session).analyze_theme(
            DemandThemeAnalysisCreate(
                organization_id=uuid4(),
                name="Foreign theme",
                category="invalid",
                signal_ids=[signal.id],
                summary="Must remain tenant isolated.",
            ),
            user.id,
        )


def test_authenticated_opportunity_api_and_dashboard(
    db_session: Session, client: TestClient
) -> None:
    organization, user, signals = reviewed_signals(db_session)
    payload = candidate_payload(organization.id, [signal.id for signal in signals[:3]])
    headers = {"X-Actor-ID": str(user.id)}
    response = client.post(
        "/api/v1/opportunities", json=payload.model_dump(mode="json"), headers=headers
    )
    assert response.status_code == 201
    candidate = response.json()
    evidence = client.get(
        f"/api/v1/opportunities/{candidate['id']}/evidence",
        params={"organization_id": str(organization.id)},
    )
    assessment = client.get(
        f"/api/v1/opportunities/{candidate['id']}/assessment",
        params={"organization_id": str(organization.id)},
    )
    dashboard = client.get(
        "/api/v1/opportunity-discovery-dashboard",
        params={"organization_id": str(organization.id)},
    )
    assert evidence.status_code == assessment.status_code == dashboard.status_code == 200
    assert len(evidence.json()) == 3
    assert assessment.json()["demand_strength"] == "strong"
    assert dashboard.json()["review_queue"][0]["id"] == candidate["id"]
