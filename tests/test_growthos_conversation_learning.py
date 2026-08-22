from datetime import UTC, datetime
from uuid import uuid4

import pytest
from commerce_os.ai_runtime.models import AIRequestStatus
from commerce_os.growth.conversation_learning_models import (
    GrowthMessagePerformanceObservation,
)
from commerce_os.growth.conversation_learning_schemas import (
    MessagePerformanceCreate,
    ObjectionRecordCreate,
    SalesLearningSignalCreate,
)
from commerce_os.growth.conversation_learning_services import (
    GrowthConversationLearningService,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import GrowthOutreachDraft, SalesConversationAnalysis
from commerce_os.growth.revenue_schemas import SalesAnalysisCreate
from commerce_os.growth.revenue_services import GrowthRevenueService, scoped_revenue
from commerce_os.learning.models import LearningObservation
from commerce_os.shared.database import get_session
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.growth_learning_orchestration import create_growth_sales_learning_signal
from apps.api.main import app
from tests.test_growthos_revenue_engine import (
    completed_request,
    prospect_and_evidence,
)


def conversation_foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    from tests.test_ai_research_operationalization import foundation

    entities = foundation(session, slug)
    organization, user, *_ = entities
    prospect, _ = prospect_and_evidence(session, entities)
    ai_request = completed_request(session, entities, "analysis")
    analysis = GrowthRevenueService(session).create_sales_analysis(
        SalesAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            conversation_reference=f"manual:{slug}",
            intent="price_objection",
            sentiment="interested_but_cautious",
            objection="The price is higher than expected.",
            buying_stage="considering",
            recommended_action="Explain scope and ask which outcome matters most.",
            suggested_reply="Draft a concise scope explanation for human review.",
            ai_request_id=ai_request.id,
            customer_reply="This looks useful, but the price is higher than I expected.",
            buying_signal="conditional_positive",
            objection_type="price",
            urgency="medium",
        ),
        user.id,
    )
    return entities, prospect, ai_request, analysis


def test_conversation_analysis_lifecycle_and_ai_authority(db_session: Session) -> None:
    entities, prospect, ai_request, analysis = conversation_foundation(
        db_session, "conversation-lifecycle"
    )
    organization, user, *_ = entities
    service = GrowthConversationLearningService(db_session)
    assert analysis.status == "draft" and analysis.urgency == "medium"
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_analysis(analysis, "accepted", user.id)
    analysis = service.transition_analysis(analysis, "reviewed", user.id)
    analysis = service.transition_analysis(analysis, "accepted", user.id)
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_analysis(analysis, "reviewed", user.id)

    ai_request.status = AIRequestStatus.READY
    db_session.commit()
    with pytest.raises(GrowthError, match="completed governed AI request"):
        GrowthRevenueService(db_session).create_sales_analysis(
            SalesAnalysisCreate(
                organization_id=organization.id,
                prospect_id=prospect.id,
                conversation_reference="manual:invalid-authority",
                intent="question",
                sentiment="neutral",
                buying_stage="unknown",
                recommended_action="Human review.",
                suggested_reply="Draft only.",
                ai_request_id=ai_request.id,
                customer_reply="Can you tell me more?",
                buying_signal="unknown",
                urgency="low",
            ),
            user.id,
        )


def test_objection_and_learning_signal_reuse_closed_loop(db_session: Session) -> None:
    entities, _, _, analysis = conversation_foundation(db_session, "conversation-learning")
    organization, user, *_ = entities
    service = GrowthConversationLearningService(db_session)
    with pytest.raises(GrowthError, match="human-reviewed"):
        service.create_objection(
            ObjectionRecordCreate(
                organization_id=organization.id,
                analysis_id=analysis.id,
                customer_segment="Independent studio",
                objection_type="price",
            ),
            user.id,
        )
    analysis = service.transition_analysis(analysis, "reviewed", user.id)
    objection = service.create_objection(
        ObjectionRecordCreate(
            organization_id=organization.id,
            analysis_id=analysis.id,
            customer_segment="Independent studio",
            objection_type="price",
            outcome="unresolved",
        ),
        user.id,
    )
    assert objection.original_message == analysis.customer_reply
    with pytest.raises(GrowthError, match="human-accepted"):
        create_growth_sales_learning_signal(
            db_session,
            SalesLearningSignalCreate(
                organization_id=organization.id,
                analysis_id=analysis.id,
                objection_record_id=objection.id,
                signal_type="objection_pattern",
                insight="Price needs context.",
                future_recommendation="Test a clearer scope explanation.",
                confidence=0.8,
            ),
            user.id,
        )
    analysis = service.transition_analysis(analysis, "accepted", user.id)
    signal = create_growth_sales_learning_signal(
        db_session,
        SalesLearningSignalCreate(
            organization_id=organization.id,
            analysis_id=analysis.id,
            objection_record_id=objection.id,
            signal_type="objection_pattern",
            insight="Price objections appear with unclear scope.",
            future_recommendation="Test a clearer scope explanation in future drafts.",
            confidence=0.8,
        ),
        user.id,
    )
    observation = db_session.get(LearningObservation, signal.learning_observation_id)
    assert observation is not None
    assert observation.source_domain == "growth"
    assert observation.source_record_id == analysis.id
    assert observation.observation_metadata["source_truth_modified"] is False

    with pytest.raises(ValidationError):
        ObjectionRecordCreate(
            organization_id=organization.id,
            analysis_id=analysis.id,
            customer_segment="Independent studio",
            objection_type="unsupported",  # type: ignore[arg-type]
        )


def test_message_performance_dashboard_tenant_and_append_only(db_session: Session) -> None:
    entities, prospect, ai_request, analysis = conversation_foundation(
        db_session, "conversation-dashboard"
    )
    organization, user, *_ = entities
    draft = GrowthOutreachDraft(
        organization_id=organization.id,
        prospect_id=prospect.id,
        growth_gift_id=uuid4(),
        channel="email",
        subject="A specific observation",
        body="Founder-approved message recorded after manual sending.",
        tone="thoughtful",
        evidence_used=[],
        status="sent",
        ai_request_id=ai_request.id,
        approval_request_id=uuid4(),
        subject_options=["A specific observation"],
        opening_sentence="I noticed a specific issue.",
        personalized_context="Evidence context.",
        problem_observation="Observed friction.",
        gift_explanation="A small preview.",
        soft_cta="Would this be useful?",
    )
    db_session.add(draft)
    db_session.commit()
    service = GrowthConversationLearningService(db_session)
    observation = service.create_message_performance(
        MessagePerformanceCreate(
            organization_id=organization.id,
            outreach_draft_id=draft.id,
            customer_segment="Independent studio",
            message_strategy="Specific observation plus Growth Gift",
            outcome="positive",
            observed_at=datetime.now(UTC),
            confidence=1,
            metadata={"source": "founder_supplied_outcome"},
        ),
        user.id,
    )
    dashboard = service.dashboard(organization.id)
    assert dashboard.total_conversations == 1
    assert dashboard.positive_signals == 0
    assert dashboard.best_performing_messages[0].positive_or_converted == 1
    observation.outcome = "lost"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()

    other_entities, *_ = conversation_foundation(db_session, "conversation-other")
    with pytest.raises(GrowthError):
        scoped_revenue(
            db_session,
            SalesConversationAnalysis,
            analysis.id,
            other_entities[0].id,
        )
    assert (
        db_session.scalar(
            select(GrowthMessagePerformanceObservation).where(
                GrowthMessagePerformanceObservation.id == observation.id
            )
        )
        is not None
    )


def test_sales_knowledge_api_requires_authentication(db_session: Session) -> None:
    entities, *_ = conversation_foundation(db_session, "conversation-api")

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        denied = client.get(
            f"/api/v1/growth-sales-knowledge-dashboard?organization_id={entities[0].id}"
        )
    app.state.auth_test_bypass = True
    with TestClient(app) as client:
        allowed = client.get(
            f"/api/v1/growth-sales-knowledge-dashboard?organization_id={entities[0].id}"
        )
    app.dependency_overrides.clear()
    app.state.auth_test_bypass = False
    assert denied.status_code == 401
    assert allowed.status_code == 200
