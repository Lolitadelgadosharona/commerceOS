from datetime import UTC, datetime

import pytest
from commerce_os.decision.customer_value_schemas import CustomerValueCreate
from commerce_os.decision.customer_value_services import CustomerValueService
from commerce_os.decision.sales_support_models import SupportCaseIntelligence
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import AuditLog, Organization
from commerce_os.intelligence.customer_360_schemas import JourneyEventCreate
from commerce_os.intelligence.customer_360_services import Customer360Service
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.revenue_conversation_schemas import (
    EvidenceReference,
    IntentJourneyCreate,
    IntentJourneyTransition,
    SalesIntentCreate,
    SupportLearningCreate,
)
from commerce_os.intelligence.revenue_conversation_services import RevenueConversationService
from commerce_os.operations.conversation_models import ConversationThread, ThreadStatus
from commerce_os.operations.models import Customer, SalesOpportunity
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Revenue {slug}", slug=f"revenue-{slug}")
    session.add(organization)
    session.flush()
    customer = Customer(
        organization_id=organization.id,
        display_name="Evidence Customer",
        status="active",
        attributes={},
    )
    session.add(customer)
    session.flush()
    thread = ConversationThread(
        organization_id=organization.id,
        customer_id=customer.id,
        channel="website",
        status=ThreadStatus.OPEN,
        priority="normal",
    )
    session.add(thread)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"revenue-{slug}@example.com",
        display_name="Intelligence Reviewer",
        password="correct horse battery staple",
    )
    event = Customer360Service(session).create_event(
        JourneyEventCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            event_type="purchase_intent",
            source="conversation-observation",
            reference_id=f"event-{slug}",
            metadata={"thread_id": str(thread.id)},
            occurred_at=datetime.now(UTC),
            confidence=0.85,
        ),
        user.id,
    )
    return organization, customer, thread, user, event


def test_journey_events_are_append_only_and_audited(db_session: Session) -> None:
    _, _, _, _, event = foundation(db_session, "append")
    event.confidence = 0.5
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    assert "intelligence.customer_journey_event.appended" in set(
        db_session.scalars(select(AuditLog.action))
    )


def test_intent_lifecycle_requires_traceable_evidence(db_session: Session) -> None:
    organization, customer, _, user, event = foundation(db_session, "intent")
    service = RevenueConversationService(db_session)
    with pytest.raises(IntelligenceScopeError, match="requires evidence"):
        service.create_journey(
            IntentJourneyCreate(
                organization_id=organization.id,
                customer_id=customer.id,
                status="interested",
                confidence=0.5,
            ),
            user.id,
        )
    journey = service.create_journey(
        IntentJourneyCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            status="unknown",
            confidence=0,
        ),
        user.id,
    )
    journey = service.transition_journey(
        journey,
        IntentJourneyTransition(
            status="high_intent",
            evidence_references=[
                EvidenceReference(reference_type="journey_event", reference_id=event.id)
            ],
            confidence=0.85,
        ),
        user.id,
    )
    assert journey.status == "high_intent"


def test_sales_signal_is_advisory_and_does_not_create_opportunity(db_session: Session) -> None:
    organization, customer, _, user, event = foundation(db_session, "sales")
    before = db_session.scalar(select(func.count()).select_from(SalesOpportunity))
    signal = RevenueConversationService(db_session).create_sales_signal(
        SalesIntentCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            evidence_references=[
                EvidenceReference(reference_type="journey_event", reference_id=event.id)
            ],
            intent_type="purchase_intent",
            confidence=0.8,
            recommendation="A human may review the conversation context.",
        ),
        user.id,
    )
    after = db_session.scalar(select(func.count()).select_from(SalesOpportunity))
    assert signal.recommendation.startswith("A human")
    assert before == after == 0


def test_value_assessment_preserves_finance_separation(db_session: Session) -> None:
    organization, customer, _, _, _ = foundation(db_session, "value")
    assessment = CustomerValueService(db_session).create(
        CustomerValueCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            revenue_indicator=70,
            margin_indicator=60,
            repeat_probability=0.6,
            strategic_potential=80,
            risk_indicator=20,
            contribution_potential=75,
            risk_indicators=["support_frequency"],
            confidence=0.7,
        )
    )
    assert assessment.formula_version.endswith("advisory")
    assert "actual_revenue" not in assessment.__table__.columns
    assert "actual_ltv" not in assessment.__table__.columns


def test_support_learning_is_read_only_advice_and_tenant_scoped(db_session: Session) -> None:
    first = foundation(db_session, "support-a")
    second = foundation(db_session, "support-b")
    organization, _, thread, user, _ = first
    issue = SupportCaseIntelligence(
        organization_id=organization.id,
        conversation_id=thread.id,
        issue_category="quality",
        severity="medium",
        customer_impact="Customer needed clarification.",
        risk_level="low",
        recommended_resolution="Human review.",
    )
    db_session.add(issue)
    db_session.commit()
    service = RevenueConversationService(db_session)
    signal = service.create_support_learning(
        SupportLearningCreate(
            organization_id=organization.id,
            source_issue_id=issue.id,
            customer_impact="Customer needed clearer usage guidance.",
            root_cause_category="product_usage",
            recommendation="Review documentation; do not modify Product Truth automatically.",
        ),
        user.id,
    )
    assert signal.root_cause_category == "product_usage"
    with pytest.raises(IntelligenceScopeError, match="not found"):
        service.create_support_learning(
            SupportLearningCreate(
                organization_id=second[0].id,
                source_issue_id=issue.id,
                customer_impact="Forbidden",
                root_cause_category="other",
                recommendation="Forbidden",
            ),
            second[3].id,
        )


def test_dashboard_is_read_only_and_requires_authentication(
    db_session: Session, client: TestClient
) -> None:
    organization, customer, _, user, event = foundation(db_session, "dashboard")
    service = RevenueConversationService(db_session)
    journey = service.create_journey(
        IntentJourneyCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            status="aware",
            evidence_references=[
                EvidenceReference(reference_type="journey_event", reference_id=event.id)
            ],
            confidence=0.7,
        ),
        user.id,
    )
    projection = service.dashboard(organization.id)
    assert projection.intent_distribution[journey.status] == 1
    app.state.auth_test_bypass = False
    try:
        response = client.get(
            "/api/v1/revenue-conversation-dashboard",
            params={"organization_id": str(organization.id)},
        )
        assert response.status_code == 401
    finally:
        app.state.auth_test_bypass = True
