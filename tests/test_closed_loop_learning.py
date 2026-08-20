from datetime import UTC, datetime

import pytest
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.intelligence.models import (
    CustomerSignal,
    Sentiment,
    Severity,
    SignalSource,
    SignalSourceType,
    SignalType,
)
from commerce_os.learning.schemas import (
    ConclusionCreate,
    ConclusionTransition,
    EvidenceLinkInput,
    HypothesisCreate,
    LearningObservationCreate,
    PriorityCreate,
    PriorityInputs,
    RecommendationCreate,
)
from commerce_os.learning.services import ClosedLoopLearningService, LearningError
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app


def foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Learning {slug}", slug=f"learning-{slug}")
    session.add(organization)
    session.flush()
    source = SignalSource(
        organization_id=organization.id,
        source_type=SignalSourceType.SUPPORT,
        name=f"Support {slug}",
        description="Supplied evidence",
        is_active=True,
    )
    session.add(source)
    session.flush()
    signals = []
    for index in range(3):
        signal = CustomerSignal(
            organization_id=organization.id,
            signal_source_id=source.id,
            source_type=SignalSourceType.SUPPORT,
            source_reference=f"{slug}-{index}",
            customer_id=None,
            signal_type=SignalType.TRUST_CONCERN,
            content_reference=f"evidence:{index}",
            sentiment=Sentiment.NEGATIVE,
            severity=Severity.HIGH,
            confidence=0.8,
        )
        session.add(signal)
        signals.append(signal)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"learning-{slug}@example.com",
        display_name="Learning Reviewer",
        password="correct horse battery staple",
    )
    return organization, signals, user


def observations(session: Session, entities):  # type: ignore[no-untyped-def]
    organization, signals, user = entities
    service = ClosedLoopLearningService(session)
    return [
        service.create_observation(
            LearningObservationCreate(
                organization_id=organization.id,
                source_type="customer_signal",
                source_record_id=signal.id,
                observation_type="recurring_trust_question",
                observed_at=datetime.now(UTC),
                evidence_reference=f"customer-signal:{signal.id}",
                confidence=0.8,
                metadata={"copied_truth": False},
            ),
            user.id,
        )
        for signal in signals
    ]


def test_observations_append_only_tenant_scoped_and_causality_guarded(db_session: Session) -> None:
    first = foundation(db_session, "a")
    second = foundation(db_session, "b")
    items = observations(db_session, first)
    items[0].confidence = 0.2
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    with pytest.raises(LearningError, match="not found"):
        ClosedLoopLearningService(db_session).create_observation(
            LearningObservationCreate(
                organization_id=second[0].id,
                source_type="customer_signal",
                source_record_id=first[1][0].id,
                observation_type="forbidden",
                observed_at=datetime.now(UTC),
                evidence_reference="forbidden",
            ),
            second[2].id,
        )
    with pytest.raises(LearningError, match="causal certainty"):
        ClosedLoopLearningService(db_session).create_hypothesis(
            HypothesisCreate(
                organization_id=first[0].id,
                hypothesis="This proves low trust causes refunds.",
                target_type="listing",
                category="trust",
                evidence_links=[
                    EvidenceLinkInput(observation_id=items[0].id, evidence_role="supporting")
                ],
                evidence_coverage=0.8,
                confidence=0.8,
                methodology_version="deterministic-v1",
            ),
            first[2].id,
        )


def test_full_feedback_loop_priority_queue_and_boundaries(db_session: Session) -> None:
    entities = foundation(db_session, "loop")
    organization, _, user = entities
    items = observations(db_session, entities)
    service = ClosedLoopLearningService(db_session)
    hypothesis = service.create_hypothesis(
        HypothesisCreate(
            organization_id=organization.id,
            hypothesis="Repeated questions may be associated with insufficient trust evidence.",
            target_type="listing",
            category="customer_trust",
            evidence_links=[
                EvidenceLinkInput(observation_id=items[0].id, evidence_role="supporting"),
                EvidenceLinkInput(observation_id=items[1].id, evidence_role="supporting"),
                EvidenceLinkInput(observation_id=items[2].id, evidence_role="contradicting"),
            ],
            evidence_coverage=0.8,
            confidence=0.75,
            methodology_version="deterministic-v1",
        ),
        user.id,
    )
    hypothesis = service.transition_hypothesis(hypothesis, "under_review", user.id)
    hypothesis = service.transition_hypothesis(hypothesis, "supported", user.id)
    conclusion = service.create_conclusion(
        ConclusionCreate(
            organization_id=organization.id,
            hypothesis_id=hypothesis.id,
            conclusion=(
                "Evidence supports testing clearer trust content; causation is not established."
            ),
            confidence=0.75,
            evidence_coverage=0.8,
            methodology_version="deterministic-v1",
        ),
        user.id,
    )
    conclusion = service.transition_conclusion(
        conclusion,
        ConclusionTransition(status="supported", review_metadata={"human_review": True}),
        user.id,
    )
    recommendation = service.create_recommendation(
        RecommendationCreate(
            organization_id=organization.id,
            conclusion_id=conclusion.id,
            target_type="listing",
            recommendation="Test clearer trust evidence in a reviewed listing draft.",
            rationale="Two observations support the pattern and one contradicts it.",
        ),
        user.id,
    )
    priority = service.assess_priority(
        PriorityCreate(
            organization_id=organization.id,
            recommendation_id=recommendation.id,
            inputs=PriorityInputs(
                expected_commercial_impact=90,
                evidence_confidence=80,
                customer_frequency=85,
                customer_severity=80,
                financial_impact=90,
                refund_risk=85,
                reversibility=90,
                testability=90,
            ),
        ),
        user.id,
    )
    assert priority.calculated_score >= 75
    assert "dispute_risk" in priority.missing_inputs
    approvals_before = db_session.scalar(select(func.count()).select_from(ApprovalRequest))
    _, high_risk = service.review_queue_priority(recommendation)
    queue = DecisionQueueService(db_session).create(
        DecisionQueueCreate(
            organization_id=organization.id,
            title="Review learning improvement",
            domain="learning",
            reason=recommendation.rationale,
            priority="critical" if high_risk else "high",
            required_action="review",
        )
    )
    recommendation = service.attach_decision_queue(recommendation, queue.id, user.id)
    assert recommendation.decision_queue_item_id is not None
    assert db_session.scalar(select(func.count()).select_from(DecisionQueueItem)) == 1
    assert (
        db_session.scalar(select(func.count()).select_from(ApprovalRequest))
        == approvals_before
        == 0
    )
    chain = service.feedback_loop(recommendation.id, organization.id)
    assert len(chain.observation) == 3 and chain.priority is not None
    assert chain.missing_stages == ["future_execution", "new_evidence"]
    dashboard = service.dashboard(organization.id)
    assert dashboard.advisory and dashboard.supported_conclusions == 1


def test_supported_state_requires_minimum_evidence_and_authentication(
    db_session: Session, client: TestClient
) -> None:
    entities = foundation(db_session, "minimum")
    organization, _, user = entities
    item = observations(db_session, entities)[0]
    service = ClosedLoopLearningService(db_session)
    hypothesis = service.create_hypothesis(
        HypothesisCreate(
            organization_id=organization.id,
            hypothesis="One signal may be associated with a listing gap.",
            target_type="listing",
            category="information_gap",
            evidence_links=[EvidenceLinkInput(observation_id=item.id, evidence_role="supporting")],
            evidence_coverage=0.4,
            confidence=0.4,
            methodology_version="deterministic-v1",
        ),
        user.id,
    )
    hypothesis = service.transition_hypothesis(hypothesis, "under_review", user.id)
    with pytest.raises(LearningError, match="two supporting"):
        service.transition_hypothesis(hypothesis, "supported", user.id)
    app.state.auth_test_bypass = False
    try:
        assert (
            client.get(
                "/api/v1/learning-dashboard", params={"organization_id": organization.id}
            ).status_code
            == 401
        )
    finally:
        app.state.auth_test_bypass = True
