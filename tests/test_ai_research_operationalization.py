import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.ai_runtime.schemas import CapabilityCreate, ProviderCreate
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.governance.models import ApprovalRequest, AuditLog, Organization, PrincipalType
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.intelligence.research_models import (
    ResearchAnalysis,
    ResearchEvidenceCitation,
    ResearchRun,
)
from commerce_os.intelligence.research_schemas import (
    ResearchRunCreate,
    ResearchRunEvidenceInput,
)
from commerce_os.intelligence.research_services import ResearchAnalystService, scoped_research
from commerce_os.intelligence.voice_models import CustomerPainCluster
from commerce_os.operations.execution_models import ProductLaunch
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import execute_research_run


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Research {slug}", slug=f"research-{slug}")
    session.add(organization)
    session.commit()
    auth = AuthenticationService(session)
    user = auth.create_user(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="Research Owner",
        password="correct horse battery staple",
    )
    worker = auth.create_user(
        organization_id=organization.id,
        email=f"worker-{slug}@example.com",
        display_name="Research Worker",
        password="service credential only",
        principal_type=PrincipalType.SERVICE,
    )
    runtime = AIRuntimeService(session)
    provider = runtime.create_provider(
        ProviderCreate(
            organization_id=organization.id,
            provider_identity=f"deterministic_{slug}",
            display_name="Deterministic Research",
            availability_state="available",
            provider_version="v1",
            cost_metadata={},
            runtime_configuration={"max_retries": 0},
        ),
        user.id,
    )
    capability = runtime.create_capability(
        CapabilityCreate(
            organization_id=organization.id,
            provider_id=provider.id,
            model_identity="research-model-v1",
            capability_type="text_generation",
            model_version="v1",
            available=True,
            cost_metadata={"currency": "USD"},
        ),
        user.id,
    )
    evidence = CustomerPainCluster(
        organization_id=organization.id,
        name="Trust evidence gap",
        category="trust",
        description="Customers request stronger proof.",
        severity_score=70,
        confidence_score=0.8,
        status="active",
        scoring_evidence={"frequency": 8},
    )
    session.add(evidence)
    session.commit()
    return organization, user, worker, provider, capability, evidence


def create_run(session: Session, entities, evidence: bool = True):  # type: ignore[no-untyped-def]
    organization, user, _, _, capability, item = entities
    references = (
        [
            ResearchRunEvidenceInput(
                evidence_type="pain_cluster",
                evidence_id=item.id,
                source_reference=f"pain-cluster:{item.id}",
                confidence=0.8,
            )
        ]
        if evidence
        else []
    )
    return ResearchAnalystService(session).create_run(
        ResearchRunCreate(
            organization_id=organization.id,
            research_type="customer_pain_analysis",
            objective="Analyze trust concerns from supplied evidence.",
            capability_id=capability.id,
            evidence=references,
        ),
        user.id,
    )


RESPONSE = {
    "summary": "Trust evidence may be insufficient; human review is recommended.",
    "key_findings": ["Customers repeatedly request proof."],
    "evidence_used": ["pain-cluster"],
    "customer_language": ["Can I trust this?"],
    "confidence": 0.8,
    "risks": ["Evidence coverage is limited."],
    "unanswered_questions": ["Does this generalize across channels?"],
}


def test_operational_research_worker_grounding_and_authority(db_session: Session) -> None:
    entities = foundation(db_session, "complete")
    organization, user, worker, provider, _, _ = entities
    service = ResearchAnalystService(db_session)
    run = service.queue_run(create_run(db_session, entities), user.id)
    before = {
        "opportunity": db_session.scalar(select(func.count()).select_from(MarketOpportunity)),
        "launch": db_session.scalar(select(func.count()).select_from(ProductLaunch)),
        "approval": db_session.scalar(select(func.count()).select_from(ApprovalRequest)),
    }
    run = execute_research_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter(RESPONSE)},
    )
    assert run.status == "completed" and run.analysis_id and run.ai_request_id
    analysis = db_session.get(ResearchAnalysis, run.analysis_id)
    assert analysis is not None and analysis.output_classification == "analysis"
    citation = db_session.scalar(select(ResearchEvidenceCitation))
    assert citation is not None and citation.citation_location == "structured_output.evidence_used"
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
            title="Review research",
            domain="intelligence",
            reason=run.objective,
            priority="high",
            required_action="review",
        )
    )
    run = service.attach_decision_queue(run, queue.id, user.id)
    assert (
        run.decision_queue_item_id
        and db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    )
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert {"research.run.created", "research.run.started", "research.run.completed"} <= actions


def test_missing_evidence_invalid_output_tenant_and_terminal_rules(db_session: Session) -> None:
    entities = foundation(db_session, "invalid")
    organization, user, worker, provider, _, _ = entities
    other = foundation(db_session, "other")
    service = ResearchAnalystService(db_session)
    empty = create_run(db_session, entities, evidence=False)
    with pytest.raises(IntelligenceValidationError, match="missing_evidence"):
        service.queue_run(empty, user.id)
    run = service.queue_run(create_run(db_session, entities), user.id)
    with pytest.raises(IntelligenceScopeError):
        scoped_research(db_session, ResearchRun, run.id, other[0].id)
    failed = execute_research_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={
            provider.provider_identity: DeterministicProviderAdapter({"summary": "incomplete"})
        },
    )
    assert failed.status == "failed" and failed.failure_reason
    with pytest.raises(IntelligenceValidationError):
        service.cancel_run(failed, user.id)


def test_research_templates_and_unauthenticated_api(db_session: Session) -> None:
    assert len(ResearchAnalystService.templates()) == 5
    entities = foundation(db_session, "auth")
    organization = entities[0]
    from commerce_os.shared.database import get_session

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(f"/api/v1/research-runs?organization_id={organization.id}")
    app.dependency_overrides.clear()
    assert response.status_code == 401
