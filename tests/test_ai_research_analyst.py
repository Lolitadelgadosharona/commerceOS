from datetime import UTC, datetime

import pytest
from commerce_os.ai_runtime.schemas import AIRequestCreate
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import AuditLog, Organization
from commerce_os.intelligence.connector_schemas import ConnectorCreate, MarketDataRecordCreate
from commerce_os.intelligence.connector_services import MarketConnectorService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.intelligence.research_models import ResearchAnalysis
from commerce_os.intelligence.research_schemas import (
    CustomerPainResearchCreate,
    OpportunityResearchBriefCreate,
    ResearchAnalysisCreate,
    ResearchCitationCreate,
)
from commerce_os.intelligence.research_services import ResearchAnalystService
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Research {slug}", slug=f"research-{slug}")
    session.add(organization)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"research-{slug}@example.com",
        display_name="Research Reviewer",
        password="correct horse battery staple",
    )
    request = AIRuntimeService(session).create_request(
        AIRequestCreate(
            organization_id=organization.id,
            purpose="Analyze existing supplied evidence",
            context_type="research_analysis",
            context_reference=f"research:{slug}",
        ),
        user.id,
    )
    connector_service = MarketConnectorService(session)
    connector = connector_service.create_connector(
        ConnectorCreate(
            organization_id=organization.id,
            name=f"Research fixture {slug}",
            platform="fixture",
            connector_type="news",
            authentication_state="not_required",
        )
    )
    connector_service.transition_connector(connector, "configured")
    connector_service.transition_connector(connector, "ready")
    evidence = connector_service.store_record(
        MarketDataRecordCreate(
            organization_id=organization.id,
            source_id=connector.id,
            external_reference=f"fixture://research/{slug}",
            content_type="research_fixture",
            raw_content="Existing evidence supplied by the test.",
            captured_at=datetime.now(UTC),
        )
    )
    return organization, user, request, evidence


def analysis_payload(organization, request, analysis_type="customer_pain"):  # type: ignore[no-untyped-def]
    return ResearchAnalysisCreate(
        organization_id=organization.id,
        ai_request_id=request.id,
        analysis_type=analysis_type,
        output_classification="analysis",
        output_summary="Draft interpretation of cited evidence.",
        confidence=0.72,
        methodology_version="research-method-v1",
    )


def citation_payload(organization, analysis, evidence):  # type: ignore[no-untyped-def]
    return ResearchCitationCreate(
        organization_id=organization.id,
        analysis_id=analysis.id,
        evidence_type="market_data_record",
        evidence_id=evidence.id,
        source_reference=evidence.external_reference,
        citation_note="Supports the stated customer pain pattern.",
        relevance_score=0.9,
    )


def test_analysis_requires_citations_and_human_review(db_session: Session) -> None:
    organization, user, request, evidence = foundation(db_session, "lifecycle")
    service = ResearchAnalystService(db_session)
    analysis = service.create_analysis(analysis_payload(organization, request), user.id)
    with pytest.raises(IntelligenceValidationError, match="citation"):
        service.transition_analysis(analysis, "in_review", user.id)
    citation = service.add_citation(citation_payload(organization, analysis, evidence), user.id)
    assert citation.evidence_id == evidence.id
    analysis = service.transition_analysis(analysis, "in_review", user.id)
    analysis = service.transition_analysis(analysis, "reviewed", user.id)
    assert analysis.reviewed_by == user.id
    assert {
        "research.analysis.created",
        "research.citation.created",
        "research.analysis.reviewed",
    } <= set(db_session.scalars(select(AuditLog.action)))


def test_customer_pain_analysis_is_cited_and_tenant_scoped(db_session: Session) -> None:
    organization, user, request, evidence = foundation(db_session, "pain")
    other, _, _, _ = foundation(db_session, "other")
    service = ResearchAnalystService(db_session)
    analysis = service.create_analysis(analysis_payload(organization, request), user.id)
    service.add_citation(citation_payload(organization, analysis, evidence), user.id)
    pain = service.create_customer_pain(
        CustomerPainResearchCreate(
            organization_id=organization.id,
            analysis_id=analysis.id,
            pain_patterns=["Repeated packaging complaints"],
            customer_needs=["Damage protection"],
            objections=["Low confidence in shipping quality"],
            motivations=["Receive an intact product"],
            language_themes=["arrived damaged"],
        ),
        user.id,
    )
    assert pain.language_themes == ["arrived damaged"]
    with pytest.raises(IntelligenceScopeError):
        service.add_citation(
            citation_payload(other, analysis, evidence).model_copy(
                update={"organization_id": other.id}
            ),
            user.id,
        )


def test_opportunity_brief_composes_existing_record_without_creation(db_session: Session) -> None:
    organization, user, request, evidence = foundation(db_session, "brief")
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Existing opportunity",
        description="Human-created opportunity fixture",
        category="home",
        market="US",
        geography="US",
        trigger_type="customer_pain",
        timing_window="next quarter",
        status="observed",
        confidence_score=0.6,
    )
    db_session.add(opportunity)
    db_session.commit()
    service = ResearchAnalystService(db_session)
    analysis = service.create_analysis(
        analysis_payload(organization, request, "opportunity_brief"), user.id
    )
    service.add_citation(citation_payload(organization, analysis, evidence), user.id)
    before = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    brief = service.create_brief(
        OpportunityResearchBriefCreate(
            organization_id=organization.id,
            analysis_id=analysis.id,
            opportunity_id=opportunity.id,
            opportunity_summary="Advisory research draft",
            customer_problem="Existing cited customer problem",
            market_context="Supplied market context",
            competition="Incomplete competitive context",
            risks=["Evidence coverage"],
            economics_references=[{"type": "profile", "reference": "economic-profile:1"}],
            missing_information=["Validated demand"],
        ),
        user.id,
    )
    after = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    assert brief.opportunity_id == opportunity.id
    assert before == after == 1


def test_output_authority_and_confidence_validation() -> None:
    with pytest.raises(ValidationError):
        ResearchAnalysisCreate(
            organization_id="00000000-0000-0000-0000-000000000001",
            ai_request_id="00000000-0000-0000-0000-000000000002",
            analysis_type="market_insight",
            output_classification="approval",  # type: ignore[arg-type]
            output_summary="Forbidden authority",
            confidence=0.5,
            methodology_version="v1",
        )
    with pytest.raises(ValidationError):
        ResearchAnalysisCreate(
            organization_id="00000000-0000-0000-0000-000000000001",
            ai_request_id="00000000-0000-0000-0000-000000000002",
            analysis_type="market_insight",
            output_classification="analysis",
            output_summary="Invalid confidence",
            confidence=1.01,
            methodology_version="v1",
        )


def test_research_api_uses_verified_actor_and_exposes_no_execution(
    client: TestClient, db_session: Session
) -> None:
    organization, user, request, _ = foundation(db_session, "api")
    response = client.post(
        "/api/v1/research-analyses",
        headers={"X-Actor-ID": str(user.id)},
        json=analysis_payload(organization, request).model_dump(mode="json"),
    )
    assert response.status_code == 201
    assert (
        client.get(
            "/api/v1/research-analyses", params={"organization_id": organization.id}
        ).status_code
        == 200
    )
    assert client.post("/api/v1/research-analyses/execute", json={}).status_code in {404, 405, 422}
    assert db_session.scalar(select(ResearchAnalysis)).organization_id == organization.id
