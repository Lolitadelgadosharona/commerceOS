import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.governance.models import ApprovalRequest, AuditLog
from commerce_os.intelligence.discovery_models import OpportunityCandidate, OpportunityDiscoveryRun
from commerce_os.intelligence.discovery_schemas import (
    DiscoveryEvidenceInput,
    OpportunityDiscoveryRunCreate,
)
from commerce_os.intelligence.discovery_services import (
    OpportunityDiscoveryService,
    scoped_discovery,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.operations.execution_models import ProductLaunch
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import execute_opportunity_discovery_run
from tests.test_ai_research_operationalization import foundation

RESULT = {
    "title": "Proof-first trust product",
    "problem": "Customers lack credible proof.",
    "customer_segment": "Risk-conscious buyers",
    "evidence_summary": "Repeated trust concerns in supplied cluster.",
    "solution_direction": "Evidence-led product experience",
    "customer_language": ["Can I trust this?"],
    "risks": ["Limited source coverage"],
    "confidence": 0.8,
    "open_questions": ["Does it generalize?"],
    "missing_evidence": ["Marketplace validation"],
}


def create_run(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, user, _, _, capability, evidence = entities
    return OpportunityDiscoveryService(session).create_run(
        OpportunityDiscoveryRunCreate(
            organization_id=organization.id,
            discovery_type="cross_source_opportunity_discovery",
            objective="Find a grounded opportunity candidate.",
            capability_id=capability.id,
            evidence=[
                DiscoveryEvidenceInput(
                    evidence_type="pain_cluster",
                    evidence_id=evidence.id,
                    source_reference=f"pain-cluster:{evidence.id}",
                    confidence=0.8,
                )
            ],
        ),
        user.id,
    )


def test_discovery_worker_grounding_and_authority(db_session: Session) -> None:
    entities = foundation(db_session, "discovery")
    organization, user, worker, provider, _, _ = entities
    service = OpportunityDiscoveryService(db_session)
    run = service.queue(create_run(db_session, entities), user.id)
    before = {
        "opportunity": db_session.scalar(select(func.count()).select_from(MarketOpportunity)),
        "launch": db_session.scalar(select(func.count()).select_from(ProductLaunch)),
        "approval": db_session.scalar(select(func.count()).select_from(ApprovalRequest)),
    }
    run = execute_opportunity_discovery_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter(RESULT)},
    )
    assert run.status == "completed"
    candidate = db_session.scalar(
        select(OpportunityCandidate).where(OpportunityCandidate.discovery_run_id == run.id)
    )
    assert candidate is not None and candidate.advisory_score == 80 and candidate.status == "draft"
    assert candidate.evidence_references[0]["type"] == "pain_cluster"
    assert (
        db_session.scalar(select(func.count()).select_from(MarketOpportunity))
        == before["opportunity"]
    )
    assert db_session.scalar(select(func.count()).select_from(ProductLaunch)) == before["launch"]
    assert (
        db_session.scalar(select(func.count()).select_from(ApprovalRequest))
        == before["approval"]
        == 0
    )
    queue = DecisionQueueService(db_session).create(
        DecisionQueueCreate(
            organization_id=organization.id,
            title="Review AI discovered opportunity",
            domain="intelligence",
            reason=candidate.problem_statement,
            priority="high",
            required_action="review",
        )
    )
    candidate = service.mark_review(candidate, queue.id, user.id)
    assert (
        candidate.status == "review"
        and db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    )
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    assert "opportunity_discovery.run.completed" in set(db_session.scalars(select(AuditLog.action)))


def test_discovery_failure_tenant_and_terminal_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "discovery-invalid")
    organization, user, worker, provider, _, _ = entities
    other = foundation(db_session, "discovery-other")
    service = OpportunityDiscoveryService(db_session)
    run = service.queue(create_run(db_session, entities), user.id)
    with pytest.raises(IntelligenceScopeError):
        scoped_discovery(db_session, OpportunityDiscoveryRun, run.id, other[0].id)
    run = execute_opportunity_discovery_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter({"title": "malformed"})},
    )
    assert run.status == "failed" and run.failure_reason
    with pytest.raises(IntelligenceValidationError):
        service.cancel(run, user.id)


def test_discovery_templates_and_unauthenticated_api(db_session: Session) -> None:
    assert len(OpportunityDiscoveryService.templates()) == 4
    entities = foundation(db_session, "discovery-auth")
    from commerce_os.shared.database import get_session

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/opportunity-discovery-runs?organization_id={entities[0].id}"
        )
    app.dependency_overrides.clear()
    assert response.status_code == 401
