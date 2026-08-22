from uuid import uuid4

import pytest
from commerce_os.build.models import Product
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.growth.conversation_learning_schemas import SalesLearningSignalCreate
from commerce_os.growth.conversation_learning_services import (
    GrowthConversationLearningService,
)
from commerce_os.intelligence.demand_bridge_models import (
    DemandSignal,
    DemandSignalEvidence,
)
from commerce_os.intelligence.demand_bridge_schemas import DemandAggregationCreate
from commerce_os.intelligence.demand_bridge_services import DemandIntelligenceService
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.shared.database import get_session
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.growth_learning_orchestration import create_growth_sales_learning_signal
from apps.api.main import app
from tests.test_growthos_conversation_learning import conversation_foundation
from tests.test_growthos_revenue_activation import approved_request


def accepted_learning_signals(session: Session, slug: str):  # type: ignore[no-untyped-def]
    entities, _, _, analysis = conversation_foundation(session, slug)
    organization, user, *_ = entities
    service = GrowthConversationLearningService(session)
    analysis = service.transition_analysis(analysis, "reviewed", user.id)
    analysis = service.transition_analysis(analysis, "accepted", user.id)
    signals = [
        create_growth_sales_learning_signal(
            session,
            SalesLearningSignalCreate(
                organization_id=organization.id,
                analysis_id=analysis.id,
                signal_type=signal_type,
                insight=insight,
                future_recommendation="Keep the evidence available for human review.",
                confidence=confidence,
            ),
            user.id,
        )
        for signal_type, insight, confidence in [
            ("objection_pattern", "Price objections indicate unclear scope.", 0.8),
            ("buying_signal", "Conditional interest rises with clearer value.", 0.6),
        ]
    ]
    return entities, analysis, signals


def aggregate(session: Session, slug: str):  # type: ignore[no-untyped-def]
    entities, analysis, signals = accepted_learning_signals(session, slug)
    organization, user, *_ = entities
    signal = DemandIntelligenceService(session).aggregate(
        DemandAggregationCreate(
            organization_id=organization.id,
            learning_signal_ids=[item.id for item in reversed(signals)],
            customer_segment="Independent studio",
            category="pricing_clarity",
        ),
        user.id,
    )
    return entities, analysis, signals, signal


def test_accepted_conversation_learning_aggregates_traceable_demand(
    db_session: Session,
) -> None:
    products_before = db_session.scalar(select(func.count()).select_from(Product))
    opportunities_before = db_session.scalar(select(func.count()).select_from(MarketOpportunity))
    _, analysis, signals, demand = aggregate(db_session, "demand-aggregation")
    evidence = list(
        db_session.scalars(
            select(DemandSignalEvidence).where(DemandSignalEvidence.demand_signal_id == demand.id)
        )
    )
    assert demand.status == "draft"
    assert demand.source_domain == "growth"
    assert demand.source_reference_id == min((item.id for item in signals), key=str)
    assert demand.frequency == demand.evidence_count == len(evidence) == 2
    assert demand.confidence == pytest.approx(0.7)
    assert {item.source_id for item in evidence} == {item.id for item in signals}
    assert {item.evidence_text for item in evidence} == {analysis.customer_reply}
    assert db_session.scalar(select(func.count()).select_from(Product)) == products_before
    assert (
        db_session.scalar(select(func.count()).select_from(MarketOpportunity))
        == opportunities_before
    )


def test_demand_requires_accepted_complete_tenant_evidence(db_session: Session) -> None:
    entities, _, _, analysis = conversation_foundation(db_session, "demand-unreviewed")
    organization, user, *_ = entities
    analysis = GrowthConversationLearningService(db_session).transition_analysis(
        analysis, "reviewed", user.id
    )
    signal = create_growth_sales_learning_signal
    with pytest.raises(IntelligenceScopeError, match="must exist"):
        DemandIntelligenceService(db_session).aggregate(
            DemandAggregationCreate(
                organization_id=organization.id,
                learning_signal_ids=[uuid4()],
                customer_segment="Independent studio",
                category="trust",
            ),
            user.id,
        )
    assert signal is not None and analysis.status == "reviewed"


def test_demand_review_and_governance_approval_boundary(db_session: Session) -> None:
    entities, _, _, demand = aggregate(db_session, "demand-review")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    demand = service.transition(demand, "review", None, user.id)
    with pytest.raises(IntelligenceScopeError, match="Governance approval"):
        service.transition(demand, "approved", None, user.id)
    approval = approved_request(
        db_session,
        entities,
        object_type="demand_signal",
        object_id=demand.id,
        action="approve_demand_signal",
    )
    demand = service.transition(demand, "approved", approval.id, user.id)
    assert demand.status == "approved"
    assert service.dashboard(organization.id).approved_signals == 1


def test_demand_evidence_is_append_only_and_api_is_protected(db_session: Session) -> None:
    entities, _, _, demand = aggregate(db_session, "demand-api")
    organization, *_ = entities
    evidence = db_session.scalar(
        select(DemandSignalEvidence).where(DemandSignalEvidence.demand_signal_id == demand.id)
    )
    assert evidence is not None
    evidence.evidence_text = "replacement"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    restricted_user = AuthenticationService(db_session).create_user(
        organization_id=organization.id,
        email="demand-restricted@example.com",
        display_name="Restricted Reviewer",
        password="correct horse battery staple",
    )
    db_session.commit()

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        denied = client.get(
            "/api/v1/demand-intelligence-dashboard",
            params={"organization_id": organization.id},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={
                "organization_id": str(organization.id),
                "email": restricted_user.email,
                "password": "correct horse battery staple",
            },
        )
        permission_denied = client.get(
            "/api/v1/demand-intelligence-dashboard",
            params={"organization_id": organization.id},
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
    app.state.auth_test_bypass = True
    with TestClient(app) as client:
        dashboard = client.get(
            "/api/v1/demand-intelligence-dashboard",
            params={"organization_id": organization.id},
        )
        listed = client.get(
            "/api/v1/demand-signal-evidence",
            params={"organization_id": organization.id, "demand_signal_id": demand.id},
        )
    app.dependency_overrides.clear()
    app.state.auth_test_bypass = False
    assert denied.status_code == 401
    assert permission_denied.status_code == 403
    assert dashboard.status_code == 200
    assert listed.status_code == 200 and len(listed.json()) == 2
    assert db_session.get(DemandSignal, demand.id) is not None
