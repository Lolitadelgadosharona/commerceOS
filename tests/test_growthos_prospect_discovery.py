from datetime import UTC, datetime

import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.growth.discovery_models import (
    GrowthBusinessResearchResult,
    ProspectCandidate,
)
from commerce_os.growth.discovery_schemas import (
    BusinessResearchStart,
    CandidateCreate,
    DiscoveryRunCreate,
    DiscoverySourceCreate,
    QualificationInputs,
    ResearchEvidenceCreate,
)
from commerce_os.growth.discovery_services import (
    GrowthDiscoveryService,
    scoped_growth_discovery,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.intelligence.business_signal_models import BusinessDemandSignal
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.operations.models import SalesOpportunity
from commerce_os.shared.database import get_session
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import execute_growth_business_research, process_next_growth_job
from tests.test_ai_research_operationalization import foundation

AI_RESPONSE = {
    "summary": "The supplied evidence suggests booking-path friction.",
    "business_profile": {"category": "beauty studio", "location": "London"},
    "evidence_summary": [{"finding": "Booking action is difficult to locate."}],
    "potential_growth_issues": ["Booking visibility may reduce qualified enquiries."],
    "confidence": 0.8,
    "missing_information": ["Conversion analytics"],
    "risk": ["Single-site observation"],
}


def discovery_foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    entities = foundation(session, slug)
    organization, user, *_ = entities
    service = GrowthDiscoveryService(session)
    source = service.create_source(
        DiscoverySourceCreate(
            organization_id=organization.id,
            source_type="manual",
            source_name=f"Manual discovery {slug}",
            capability="evidence_reference_only",
            metadata={"external_execution": False},
        ),
        user.id,
    )
    run = service.create_run(
        DiscoveryRunCreate(
            organization_id=organization.id,
            source_id=source.id,
            query="Independent beauty studios",
            target_industry="beauty",
            target_location="London",
        ),
        user.id,
    )
    run = service.transition_run(run, "queued", user.id)
    run = service.transition_run(run, "running", user.id)
    candidate_payload = CandidateCreate(
        organization_id=organization.id,
        discovery_run_id=run.id,
        business_name="Evidence Beauty Studio",
        website="https://beauty.example",
        location="London",
        category="beauty studio",
        source_reference="manual:beauty-studio",
        confidence=0.85,
    )
    candidate = service.create_candidate(candidate_payload, user.id)
    evidence = service.create_evidence(
        ResearchEvidenceCreate(
            organization_id=organization.id,
            candidate_id=candidate.id,
            evidence_type="website_observation",
            source_url="https://beauty.example",
            observation="Booking button is not visible above the fold.",
            confidence=0.9,
            collected_at=datetime.now(UTC),
        ),
        user.id,
    )
    return entities, service, run, candidate, evidence, candidate_payload


def test_discovery_lifecycle_duplicate_and_immutable_evidence(db_session: Session) -> None:
    entities, service, run, candidate, evidence, payload = discovery_foundation(
        db_session, "growth-discovery"
    )
    duplicate = service.create_candidate(payload, entities[1].id)
    assert duplicate.id == candidate.id
    assert db_session.scalar(select(func.count()).select_from(ProspectCandidate)) == 1
    evidence.observation = "Unsupported overwrite"
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    run = service.transition_run(run, "completed", entities[1].id)
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_run(run, "queued", entities[1].id)


def test_qualification_missing_inputs_and_weighted_score(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "growth-score")
    organization, user, *_ = entities
    incomplete = service.qualify(
        candidate,
        QualificationInputs(
            organization_id=organization.id,
            pain_signal=80,
            purchase_probability=None,
            accessibility=90,
            quick_win_potential=100,
        ),
        user.id,
    )
    assert incomplete.score is None
    assert incomplete.missing_inputs == ["purchase_probability"]
    complete = service.qualify(
        candidate,
        QualificationInputs(
            organization_id=organization.id,
            pain_signal=80,
            purchase_probability=70,
            accessibility=90,
            quick_win_potential=100,
        ),
        user.id,
    )
    assert complete.score == 82
    assert candidate.status == "qualified"


def test_governed_business_research_and_intelligence_bridge(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "growth-research")
    organization, user, worker, provider, capability, _ = entities
    run = service.create_research_run(
        candidate,
        BusinessResearchStart(
            organization_id=organization.id,
            capability_id=capability.id,
        ),
        user.id,
    )
    before = {
        "market_opportunities": db_session.scalar(
            select(func.count()).select_from(MarketOpportunity)
        ),
        "sales_opportunities": db_session.scalar(
            select(func.count()).select_from(SalesOpportunity)
        ),
    }
    run = execute_growth_business_research(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter(AI_RESPONSE)},
    )
    result = db_session.scalar(
        select(GrowthBusinessResearchResult).where(
            GrowthBusinessResearchResult.research_run_id == run.id
        )
    )
    signal = db_session.scalar(select(BusinessDemandSignal))
    assert run.status == "completed" and result is not None
    assert signal is not None and signal.evidence_reference
    assert (
        db_session.scalar(select(func.count()).select_from(MarketOpportunity))
        == before["market_opportunities"]
    )
    assert (
        db_session.scalar(select(func.count()).select_from(SalesOpportunity))
        == before["sales_opportunities"]
    )


def test_growth_research_creates_durable_job_and_worker_consumes_it(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "growth-worker")
    organization, user, _, provider, capability, _ = entities
    provider.provider_identity = "deterministic_test"
    provider.runtime_configuration = {"test_response": AI_RESPONSE}
    db_session.commit()
    run = service.create_research_run(
        candidate,
        BusinessResearchStart(organization_id=organization.id, capability_id=capability.id),
        user.id,
    )
    job = db_session.scalar(select(OutboxEvent).where(OutboxEvent.correlation_id == run.id))
    assert job is not None and job.status == OutboxStatus.PENDING
    assert process_next_growth_job(db_session) is True
    db_session.refresh(run)
    db_session.refresh(job)
    assert run.status == "completed"
    assert job.status == OutboxStatus.PUBLISHED
    assert job.attempts == 1
    assert process_next_growth_job(db_session) is False


def test_growth_worker_failure_is_visible_and_bounded(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "growth-worker-fail")
    organization, user, worker, _, capability, _ = entities
    worker.status = "disabled"
    db_session.commit()
    run = service.create_research_run(
        candidate,
        BusinessResearchStart(organization_id=organization.id, capability_id=capability.id),
        user.id,
    )
    assert process_next_growth_job(db_session) is True
    job = db_session.scalar(select(OutboxEvent).where(OutboxEvent.correlation_id == run.id))
    assert job is not None and job.status == OutboxStatus.FAILED
    assert job.attempts == 1
    assert "service identity" in (job.last_error or "")


def test_tenant_and_authentication_boundaries(db_session: Session) -> None:
    entities, _, run, candidate, *_ = discovery_foundation(db_session, "growth-auth")
    other = foundation(db_session, "growth-auth-other")
    with pytest.raises(GrowthError):
        scoped_growth_discovery(db_session, ProspectCandidate, candidate.id, other[0].id)

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/prospect-discovery-runs/{run.id}?organization_id={entities[0].id}"
        )
    app.dependency_overrides.clear()
    assert response.status_code == 401

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = True
    with TestClient(app) as client:
        response = client.get(f"/api/v1/prospect-candidates?organization_id={entities[0].id}")
        dashboard = client.get(f"/api/v1/growthos-dashboard?organization_id={entities[0].id}")
    app.dependency_overrides.clear()
    app.state.auth_test_bypass = False
    assert response.status_code == 200 and len(response.json()) == 1
    assert dashboard.status_code == 200 and dashboard.json()["prospects_discovered"] == 1


def test_research_requires_evidence(db_session: Session) -> None:
    entities = foundation(db_session, "growth-no-evidence")
    organization, user, _, _, capability, _ = entities
    service = GrowthDiscoveryService(db_session)
    source = service.create_source(
        DiscoverySourceCreate(
            organization_id=organization.id,
            source_type="manual",
            source_name="No evidence source",
            capability="references_only",
        ),
        user.id,
    )
    discovery = service.create_run(
        DiscoveryRunCreate(
            organization_id=organization.id,
            source_id=source.id,
            query="test",
            target_industry="test",
            target_location="test",
        ),
        user.id,
    )
    discovery = service.transition_run(discovery, "queued", user.id)
    discovery = service.transition_run(discovery, "running", user.id)
    candidate = service.create_candidate(
        CandidateCreate(
            organization_id=organization.id,
            discovery_run_id=discovery.id,
            business_name="Missing Evidence",
            location="Test",
            category="test",
            source_reference="manual:test",
            confidence=0.5,
        ),
        user.id,
    )
    with pytest.raises(GrowthError, match="traceable candidate evidence"):
        service.create_research_run(
            candidate,
            BusinessResearchStart(organization_id=organization.id, capability_id=capability.id),
            user.id,
        )
