import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.build.models import Product, ProductTruth
from commerce_os.decision.creative_intelligence_models import (
    CreativeAngle,
    CreativeBriefRecommendation,
    CreativeIntelligenceRun,
    CreativeStrategyRecommendation,
)
from commerce_os.decision.creative_intelligence_schemas import (
    CreativeEvidenceInput,
    CreativeIntelligenceRunCreate,
)
from commerce_os.decision.creative_intelligence_services import (
    CreativeIntelligenceService,
    scoped_creative_intelligence,
)
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.governance.models import ApprovalRequest, AuditLog
from commerce_os.growth.experiment_models import DistributionCampaign
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import execute_creative_intelligence_run
from tests.test_ai_research_operationalization import foundation

OUTPUT = {
    "customer": "Risk-conscious buyers",
    "problem": "Customers lack credible proof",
    "hook": "See the evidence first",
    "message": "Evaluate proof before choosing",
    "creative_angle": "Trust through transparent evidence",
    "visual_direction": "Show sourced proof and limitations",
    "proof_points": ["Supplied customer evidence"],
    "risks": ["Limited evidence coverage"],
    "objections": ["Is this credible?"],
    "channel": "TikTok",
    "cta": "Review the evidence",
}


def create_run(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, user, _, _, capability, evidence = entities
    brand = Brand(
        organization_id=organization.id, name="Evidence Brand", slug=f"evidence-{organization.id}"
    )
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        name="Evidence Product",
        description="Draft product",
        category="test",
        brand_id=brand.id,
        status="draft",
    )
    session.add(product)
    session.commit()
    run = CreativeIntelligenceService(session).create_run(
        CreativeIntelligenceRunCreate(
            organization_id=organization.id,
            product_id=product.id,
            objective="Create grounded trust messaging.",
            template_type="trust_message",
            capability_id=capability.id,
            evidence=[
                CreativeEvidenceInput(
                    evidence_type="pain_cluster",
                    evidence_id=evidence.id,
                    source_reference=f"pain-cluster:{evidence.id}",
                    confidence=0.8,
                )
            ],
        ),
        user.id,
    )
    return run, product


def test_creative_worker_grounding_and_authority(db_session: Session) -> None:
    entities = foundation(db_session, "creative-intel")
    organization, user, worker, provider, _, _ = entities
    run, _ = create_run(db_session, entities)
    service = CreativeIntelligenceService(db_session)
    run = service.queue(run, user.id)
    before = {
        "truth": db_session.scalar(select(func.count()).select_from(ProductTruth)),
        "approval": db_session.scalar(select(func.count()).select_from(ApprovalRequest)),
        "distribution": db_session.scalar(select(func.count()).select_from(DistributionCampaign)),
    }
    run = execute_creative_intelligence_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter(OUTPUT)},
    )
    assert run.status == "completed"
    strategy = db_session.scalar(
        select(CreativeStrategyRecommendation).where(
            CreativeStrategyRecommendation.creative_run_id == run.id
        )
    )
    brief = db_session.scalar(
        select(CreativeBriefRecommendation).where(
            CreativeBriefRecommendation.creative_run_id == run.id
        )
    )
    angle = db_session.scalar(select(CreativeAngle).where(CreativeAngle.creative_run_id == run.id))
    assert (
        strategy is not None
        and strategy.confidence_score == 0.8
        and strategy.output_type == "recommendation"
    )
    assert brief is not None and brief.evidence_references[0]["type"] == "pain_cluster"
    assert angle is not None and angle.source == "governed_ai_recommendation"
    assert db_session.scalar(select(func.count()).select_from(ProductTruth)) == before["truth"]
    assert (
        db_session.scalar(select(func.count()).select_from(ApprovalRequest))
        == before["approval"]
        == 0
    )
    assert (
        db_session.scalar(select(func.count()).select_from(DistributionCampaign))
        == before["distribution"]
    )
    assert "creative_intelligence.run.completed" in set(db_session.scalars(select(AuditLog.action)))


def test_creative_failure_tenant_and_terminal_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "creative-intel-invalid")
    other = foundation(db_session, "creative-intel-other")
    organization, user, worker, provider, _, _ = entities
    run, _ = create_run(db_session, entities)
    service = CreativeIntelligenceService(db_session)
    run = service.queue(run, user.id)
    with pytest.raises(DecisionScopeError):
        scoped_creative_intelligence(db_session, CreativeIntelligenceRun, run.id, other[0].id)
    run = execute_creative_intelligence_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={
            provider.provider_identity: DeterministicProviderAdapter({"customer": "malformed"})
        },
    )
    assert run.status == "failed" and run.failure_reason
    with pytest.raises(DecisionStateError):
        service.cancel(run, user.id)


def test_creative_intelligence_unauthenticated_api(db_session: Session) -> None:
    entities = foundation(db_session, "creative-intel-auth")
    from commerce_os.shared.database import get_session

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/creative-intelligence-runs?organization_id={entities[0].id}"
        )
    app.dependency_overrides.clear()
    assert response.status_code == 401
