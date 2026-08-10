from datetime import UTC, datetime

import pytest
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.intelligence.analysis_schemas import (
    OpportunityAssessmentCreate,
    SignalAnalysisCreate,
)
from commerce_os.intelligence.analysis_services import OpportunityAnalysisService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.market_models import (
    MarketDataSource,
    MarketSignal,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Analysis {slug}", slug=slug)
    session.add(organization)
    session.flush()
    source = MarketDataSource(
        organization_id=organization.id,
        name="Supplied observation",
        platform="news",
        source_type="news",
        access_method="manual",
        reliability_score=0.8,
        status="active",
    )
    session.add(source)
    session.flush()
    signal = MarketSignal(
        organization_id=organization.id,
        source_id=source.id,
        region="US",
        category="home",
        signal_type="demand",
        title="Demand observed",
        description="Supplied signal.",
        trend_direction="rising",
        confidence_score=0.8,
        observed_at=datetime.now(UTC),
        status="validated",
    )
    opportunity = MarketOpportunity(
        organization_id=organization.id,
        title="Existing opportunity",
        description="Created independently.",
        category="home",
        market="consumer",
        geography="US",
        trigger_type="trend_shift",
        timing_window="30 days",
        status="observed",
        confidence_score=0.7,
    )
    session.add_all([signal, opportunity])
    session.flush()
    link = MarketSignalOpportunityLink(
        organization_id=organization.id,
        signal_id=signal.id,
        opportunity_id=opportunity.id,
    )
    session.add(link)
    session.commit()
    return organization, signal, opportunity


def test_analysis_assessment_evidence_and_tenant_boundaries(db_session: Session) -> None:
    organization, signal, opportunity = foundation(db_session, "analysis")
    other, _, other_opportunity = foundation(db_session, "analysis-other")
    service = OpportunityAnalysisService(db_session)
    analysis = service.analyze_signal(
        SignalAnalysisCreate(
            organization_id=organization.id,
            signal_id=signal.id,
            analysis_type="combined",
            market_impact="Moderate supplied interpretation.",
            timing_assessment="Near-term observation.",
            customer_relevance="Relevant to supplied customer need.",
            commercial_relevance="Requires further human review.",
            confidence_score=0.75,
        )
    )
    assert analysis.signal_id == signal.id
    assessment = service.assess(
        OpportunityAssessmentCreate(
            organization_id=organization.id,
            market_opportunity_id=opportunity.id,
            demand_score=80,
            timing_score=70,
            evidence_score=90,
            risk_score=20,
            commercial_score=75,
            explanation="Deterministic supplied score inputs.",
        )
    )
    assert assessment.overall_score == 78.75
    with pytest.raises(IntelligenceScopeError):
        service.analyze_signal(
            SignalAnalysisCreate(
                organization_id=other.id,
                signal_id=signal.id,
                analysis_type="combined",
                market_impact="Cross tenant.",
                timing_assessment="Cross tenant.",
                customer_relevance="Cross tenant.",
                commercial_relevance="Cross tenant.",
                confidence_score=0.5,
            )
        )
    db_session.query(MarketSignalOpportunityLink).filter(
        MarketSignalOpportunityLink.opportunity_id == other_opportunity.id
    ).delete()
    db_session.commit()
    with pytest.raises(IntelligenceValidationError):
        service.assess(
            OpportunityAssessmentCreate(
                organization_id=other.id,
                market_opportunity_id=other_opportunity.id,
                demand_score=50,
                timing_score=50,
                evidence_score=50,
                risk_score=50,
                commercial_score=50,
                explanation="Missing linked signal evidence.",
            )
        )


def test_analysis_api_report_queue_and_authority_boundaries(
    client: TestClient, db_session: Session
) -> None:
    organization, signal, opportunity = foundation(db_session, "analysis-api")
    base = {"organization_id": str(organization.id)}
    analysis_payload = base | {
        "signal_id": str(signal.id),
        "analysis_type": "combined",
        "market_impact": "Moderate impact.",
        "timing_assessment": "Review now.",
        "customer_relevance": "Relevant.",
        "commercial_relevance": "Advisory only.",
        "confidence_score": 0.8,
    }
    assert client.post("/api/v1/signal-analysis", json=analysis_payload).status_code == 201
    assert (
        client.post(
            "/api/v1/signal-analysis", json=analysis_payload | {"confidence_score": 1.1}
        ).status_code
        == 422
    )
    assessment_payload = base | {
        "market_opportunity_id": str(opportunity.id),
        "demand_score": 80,
        "timing_score": 70,
        "evidence_score": 90,
        "risk_score": 20,
        "commercial_score": 75,
        "explanation": "Deterministic score.",
    }
    assessment = client.post("/api/v1/opportunity-assessments", json=assessment_payload)
    assert assessment.status_code == 201
    assert assessment.json()["overall_score"] == 78.75
    assert (
        client.post(
            "/api/v1/opportunity-assessments",
            json=assessment_payload | {"demand_score": 101},
        ).status_code
        == 422
    )
    opportunity_count = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    report = client.post(
        "/api/v1/opportunity-reports",
        json=base
        | {
            "opportunity_id": str(opportunity.id),
            "title": "Opportunity review",
            "summary": "Supplied advisory summary.",
            "evidence_summary": "One linked market signal.",
            "recommended_actions": ["Human review"],
            "risk_summary": "Risk score is an assessment input, not Finance truth.",
        },
    )
    assert report.status_code == 201
    report_id = report.json()["id"]
    linked = client.post(
        f"/api/v1/opportunity-reports/{report_id}/decision-queue",
        json=base | {"priority": "high"},
    )
    assert linked.status_code == 201
    assert linked.json()["decision_queue_item_id"] is not None
    queue = db_session.scalar(select(DecisionQueueItem))
    assert queue is not None
    assert queue.required_action == "review"
    assert queue.approval_request_id is None
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    assert (
        db_session.scalar(select(func.count()).select_from(MarketOpportunity)) == opportunity_count
    )
    assert client.post("/api/v1/opportunity-reports/execute", json={}).status_code in {
        404,
        405,
        422,
    }
    for endpoint in ("signal-analysis", "opportunity-assessments", "opportunity-reports"):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
