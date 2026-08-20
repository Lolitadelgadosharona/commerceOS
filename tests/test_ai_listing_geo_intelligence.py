import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.build.listing_models import ListingStrategy
from commerce_os.build.models import Product, ProductTruth
from commerce_os.decision.discovery_listing_models import GeoKnowledgeAsset
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.listing_geo_intelligence_models import (
    FAQRecommendation,
    GEOContentRecommendation,
    ListingIntelligenceRun,
    ListingStrategyRecommendation,
)
from commerce_os.decision.listing_geo_intelligence_schemas import (
    ListingEvidenceInput,
    ListingIntelligenceRunCreate,
)
from commerce_os.decision.listing_geo_intelligence_services import (
    ListingIntelligenceService,
    scoped_listing_intelligence,
)
from commerce_os.governance.models import ApprovalRequest, AuditLog
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import execute_listing_intelligence_run
from tests.test_ai_research_operationalization import foundation

OUTPUT = {
    "customer_segment": "Risk-conscious buyers",
    "primary_problem": "Customers lack credible proof",
    "positioning": "Evidence-first evaluation",
    "unique_value": "Transparent limitations and proof",
    "benefits": ["Clearer evaluation"],
    "feature_translation": [{"feature": "evidence", "benefit": "informed choice"}],
    "trust_elements": ["Supplied evidence"],
    "objections": ["Is this credible?"],
    "competitive_difference": "Evidence-backed transparency",
    "entity_description": "A product evaluated through cited evidence",
    "important_attributes": ["evidence quality"],
    "customer_questions": ["What proof is available?"],
    "answer_strategy": "Answer with citations and limitations",
    "comparison_topics": ["evidence quality"],
    "expert_topics": ["evaluation criteria"],
    "citation_targets": [{"type": "pain_cluster"}],
    "missing_information": ["Broader validation"],
    "faqs": [
        {
            "question": "What evidence supports this?",
            "customer_intent": "quality",
            "answer_outline": "Summarize cited evidence and limits",
            "risk": "Do not overstate proof",
        }
    ],
}


def create_run(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, user, _, _, capability, evidence = entities
    brand = Brand(
        organization_id=organization.id, name="Listing Brand", slug=f"listing-{organization.id}"
    )
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        name="Listing Product",
        description="Draft",
        category="test",
        brand_id=brand.id,
        status="draft",
    )
    session.add(product)
    session.commit()
    run = ListingIntelligenceService(session).create_run(
        ListingIntelligenceRunCreate(
            organization_id=organization.id,
            product_id=product.id,
            objective="Create grounded listing and GEO recommendations.",
            template_type="listing_geo_combined",
            capability_id=capability.id,
            evidence=[
                ListingEvidenceInput(
                    evidence_type="pain_cluster",
                    evidence_id=evidence.id,
                    source_reference=f"pain-cluster:{evidence.id}",
                    confidence=0.8,
                )
            ],
        ),
        user.id,
    )
    return run


def test_listing_geo_worker_grounding_and_authority(db_session: Session) -> None:
    entities = foundation(db_session, "listing-geo")
    organization, user, worker, provider, _, _ = entities
    service = ListingIntelligenceService(db_session)
    run = service.queue(create_run(db_session, entities), user.id)
    before = {
        "truth": db_session.scalar(select(func.count()).select_from(ProductTruth)),
        "listing": db_session.scalar(select(func.count()).select_from(ListingStrategy)),
        "geo": db_session.scalar(select(func.count()).select_from(GeoKnowledgeAsset)),
        "approval": db_session.scalar(select(func.count()).select_from(ApprovalRequest)),
    }
    run = execute_listing_intelligence_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={provider.provider_identity: DeterministicProviderAdapter(OUTPUT)},
    )
    assert run.status == "completed"
    listing = db_session.scalar(
        select(ListingStrategyRecommendation).where(
            ListingStrategyRecommendation.listing_run_id == run.id
        )
    )
    geo = db_session.scalar(
        select(GEOContentRecommendation).where(GEOContentRecommendation.listing_run_id == run.id)
    )
    faq = db_session.scalar(
        select(FAQRecommendation).where(FAQRecommendation.listing_run_id == run.id)
    )
    assert (
        listing is not None
        and listing.confidence == 0.8
        and listing.evidence_refs[0]["type"] == "pain_cluster"
    )
    assert geo is not None and geo.missing_information == ["Broader validation"]
    assert faq is not None and faq.customer_intent == "quality"
    assert db_session.scalar(select(func.count()).select_from(ProductTruth)) == before["truth"]
    assert db_session.scalar(select(func.count()).select_from(ListingStrategy)) == before["listing"]
    assert db_session.scalar(select(func.count()).select_from(GeoKnowledgeAsset)) == before["geo"]
    assert (
        db_session.scalar(select(func.count()).select_from(ApprovalRequest))
        == before["approval"]
        == 0
    )
    assert "listing_intelligence.run.completed" in set(db_session.scalars(select(AuditLog.action)))


def test_listing_geo_failure_tenant_and_terminal_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "listing-geo-invalid")
    other = foundation(db_session, "listing-geo-other")
    organization, user, worker, provider, _, _ = entities
    service = ListingIntelligenceService(db_session)
    run = service.queue(create_run(db_session, entities), user.id)
    with pytest.raises(DecisionScopeError):
        scoped_listing_intelligence(db_session, ListingIntelligenceRun, run.id, other[0].id)
    run = execute_listing_intelligence_run(
        db_session,
        run_id=run.id,
        organization_id=organization.id,
        service_actor_id=worker.id,
        adapters={
            provider.provider_identity: DeterministicProviderAdapter(
                {"customer_segment": "malformed"}
            )
        },
    )
    assert run.status == "failed" and run.failure_reason
    with pytest.raises(DecisionStateError):
        service.cancel(run, user.id)


def test_listing_geo_unauthenticated_api(db_session: Session) -> None:
    entities = foundation(db_session, "listing-geo-auth")
    from commerce_os.shared.database import get_session

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(f"/api/v1/listing-intelligence-runs?organization_id={entities[0].id}")
    app.dependency_overrides.clear()
    assert response.status_code == 401
