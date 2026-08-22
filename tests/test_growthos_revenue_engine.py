from datetime import UTC, datetime

import pytest
from commerce_os.ai_runtime.models import AIOutputClassification, AIRequest, AIRequestStatus
from commerce_os.governance.models import AuditLog
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import (
    GrowthGift,
    GrowthOpportunityAnalysis,
    GrowthOutreachDraft,
)
from commerce_os.growth.revenue_schemas import (
    GrowthGiftCreate,
    OpportunityAnalysisCreate,
    OutreachDraftCreate,
    ProspectCreate,
    ProspectEvidenceCreate,
    SalesAnalysisCreate,
)
from commerce_os.growth.revenue_services import GrowthRevenueService, scoped_revenue
from commerce_os.shared.database import get_session
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from tests.test_ai_research_operationalization import foundation


def completed_request(session: Session, entities, classification: str) -> AIRequest:  # type: ignore[no-untyped-def]
    organization, user, _, provider, capability, _ = entities
    request = AIRequest(
        organization_id=organization.id,
        requester_id=user.id,
        purpose="GrowthOS controlled analysis",
        context_type="growth_prospect",
        context_reference="prospect:test",
        capability_id=capability.id,
        approval_request_id=None,
        status=AIRequestStatus.COMPLETED,
        output_classification=AIOutputClassification(classification),
        output_metadata={"provenance": "test"},
        failure_reason=None,
        task_type="growthos_analysis",
        selected_provider_identity=provider.provider_identity,
        selected_model_identity="research-model-v1",
    )
    session.add(request)
    session.commit()
    return request


def prospect_and_evidence(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, user, *_ = entities
    service = GrowthRevenueService(session)
    prospect = service.create_prospect(
        ProspectCreate(
            organization_id=organization.id,
            business_name="Evidence Studio",
            website="https://example.test",
            industry="beauty",
            business_type="studio",
            source="manual_research",
        ),
        user.id,
    )
    evidence = service.create_evidence(
        ProspectEvidenceCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            evidence_type="website_observation",
            source_url="https://example.test",
            observation="Booking action is difficult to locate.",
            confidence=0.9,
            collected_at=datetime.now(UTC),
        ),
        user.id,
    )
    return prospect, evidence


def test_evidence_opportunity_and_tenant_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "growthos")
    other = foundation(db_session, "growthos-other")
    organization, user, *_ = entities
    prospect, evidence = prospect_and_evidence(db_session, entities)
    opportunity = GrowthRevenueService(db_session).create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_type="booking_experience_fix",
            problem_statement="Booking friction may reduce conversion.",
            evidence_reference=[evidence.id],
            customer_impact="Customers may abandon before booking.",
            confidence=0.8,
            recommended_offer="Booking path review",
            risks=["Single observation"],
            missing_information=["Conversion analytics"],
        ),
        user.id,
    )
    assert opportunity.evidence_reference == [str(evidence.id)]
    evidence.observation = "Attempted overwrite"
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    with pytest.raises(GrowthError):
        scoped_revenue(db_session, GrowthOpportunityAnalysis, opportunity.id, other[0].id)


def test_governed_ai_and_external_communication_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "growthos-ai")
    organization, user, *_ = entities
    prospect, evidence = prospect_and_evidence(db_session, entities)
    analysis_request = completed_request(db_session, entities, "analysis")
    service = GrowthRevenueService(db_session)
    opportunity = service.create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_type="homepage_fix",
            problem_statement="Value proposition is unclear.",
            evidence_reference=[evidence.id],
            customer_impact="Visitors may not understand the offer.",
            confidence=0.75,
            recommended_offer="Homepage preview",
            ai_request_id=analysis_request.id,
        ),
        user.id,
    )
    gift = service.create_gift(
        GrowthGiftCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_id=opportunity.id,
            title="Homepage clarity preview",
            description="Evidence-based demonstration",
            before_state="Unclear hero",
            after_state="Clear outcome and action",
        ),
        user.id,
    )
    draft_request = completed_request(db_session, entities, "draft")
    draft = service.create_outreach(
        OutreachDraftCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            growth_gift_id=gift.id,
            channel="email",
            subject="A homepage observation",
            body="I prepared a small evidence-based preview for your review.",
            tone="helpful",
            evidence_used=[evidence.id],
            ai_request_id=draft_request.id,
        ),
        user.id,
    )
    draft = service.transition_outreach(draft, "human_review", user.id, None)
    with pytest.raises(GrowthError, match="approval"):
        service.transition_outreach(draft, "approved", user.id, None)
    service.create_sales_analysis(
        SalesAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            conversation_reference="conversation:1",
            intent="interested",
            sentiment="positive",
            buying_stage="considering",
            recommended_action="Human follow-up",
            suggested_reply="Draft reply for human review.",
            ai_request_id=analysis_request.id,
        ),
        user.id,
    )
    assert db_session.scalar(select(func.count()).select_from(GrowthGift)) == 1
    assert db_session.scalar(select(func.count()).select_from(GrowthOutreachDraft)) == 1
    assert "growthos.outreach.created" in set(db_session.scalars(select(AuditLog.action)))


def test_growthos_api_auth_and_dashboard(db_session: Session) -> None:
    entities = foundation(db_session, "growthos-api")
    organization, *_ = entities
    prospect_and_evidence(db_session, entities)

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = True
    with TestClient(app) as client:
        response = client.get(f"/api/v1/growthos-dashboard?organization_id={organization.id}")
        assert response.status_code == 200
        assert response.json()["prospects_discovered"] == 1
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.get(f"/api/v1/growth-prospects?organization_id={organization.id}")
        assert response.status_code == 401
    app.dependency_overrides.clear()
