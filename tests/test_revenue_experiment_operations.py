from datetime import UTC, date, datetime

import pytest
from commerce_os.governance.models import AuditLog
from commerce_os.growth.activation_schemas import (
    ProspectAssignmentCreate,
    RevenueExperimentCreate,
)
from commerce_os.growth.activation_services import RevenueActivationService
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_launch_services import RevenueLaunchService
from commerce_os.growth.revenue_operations_models import EmailWorkflowReference
from commerce_os.growth.revenue_operations_schemas import (
    CustomerFeedbackCreate,
    EmailWorkflowReferenceCreate,
    WorkspaceItemCreate,
)
from commerce_os.growth.revenue_operations_services import RevenueOperationsService
from commerce_os.learning.models import LearningObservation
from commerce_os.learning.schemas import LearningObservationCreate
from commerce_os.learning.services import ClosedLoopLearningService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.test_revenue_launch_foundation import finance_observation, launch_foundation


def operations_foundation(db_session: Session, suffix: str):
    entities, prospect, gift, pipeline, offer, payment, launch = launch_foundation(
        db_session, suffix
    )
    organization, user, *_ = entities
    prospect.status = "qualified"
    db_session.commit()
    activation = RevenueActivationService(db_session)
    experiment = activation.create_experiment(
        RevenueExperimentCreate(
            organization_id=organization.id,
            name=f"Beauty Revenue Operations {suffix}",
            description="Founder-operated Beauty revenue validation.",
            target_segment="Independent Beauty studios",
            offer_type="visibility_package",
            message_strategy="Evidence-backed Growth Gift",
            segment="Beauty",
            target_count=10,
            start_date=date(2026, 8, 22),
        ),
        user.id,
    )
    assignment = activation.assign_prospect(
        ProspectAssignmentCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            prospect_id=prospect.id,
            assigned_offer="Beauty Visibility Package",
            assigned_message="Gift-first founder draft",
        ),
        user.id,
    )
    return entities, prospect, gift, offer, payment, experiment, assignment


def test_daily_workspace_actions_are_audited(db_session: Session) -> None:
    entities, prospect, gift, _, _, experiment, _ = operations_foundation(db_session, "workspace")
    service = RevenueOperationsService(db_session)
    item = service.create_workspace_item(
        WorkspaceItemCreate(
            organization_id=entities[0].id,
            workspace_date=date(2026, 8, 22),
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            growth_gift_id=gift.id,
            priority=85,
        ),
        entities[1].id,
    )
    item = service.decide_workspace_item(
        item, "save_for_later", "Review evidence again tomorrow.", entities[1].id
    )
    item = service.decide_workspace_item(
        item, "approve", "Evidence and Gift are ready for founder action.", entities[1].id
    )
    audit = db_session.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_id == item.id, AuditLog.action == "growthos.daily_workspace.approved"
        )
        .order_by(AuditLog.timestamp.desc())
    )
    assert item.status == "approved"
    assert audit is not None
    assert audit.event_metadata["founder_action"] == "approve"


def test_email_workflow_is_reference_only_append_only_and_secret_safe(db_session: Session) -> None:
    entities, prospect, *_ = operations_foundation(db_session, "email")
    service = RevenueOperationsService(db_session)
    with pytest.raises(GrowthError, match="credentials"):
        service.create_email_reference(
            EmailWorkflowReferenceCreate(
                organization_id=entities[0].id,
                prospect_id=prospect.id,
                email_account_reference="founder-inbox-alias",
                draft_reference="draft:external-1",
                metadata={"token": "must-not-store"},
            ),
            entities[1].id,
        )
    reference = service.create_email_reference(
        EmailWorkflowReferenceCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            email_account_reference="founder-inbox-alias",
            draft_reference="draft:external-1",
            thread_reference="thread:external-1",
            metadata={"provider": "external-email-system"},
        ),
        entities[1].id,
    )
    reference.thread_reference = "overwrite"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    assert isinstance(reference, EmailWorkflowReference)


def test_only_approved_feedback_enters_existing_learning_loop(db_session: Session) -> None:
    entities, prospect, _, _, _, experiment, _ = operations_foundation(db_session, "feedback")
    service = RevenueOperationsService(db_session)
    feedback = service.create_feedback(
        CustomerFeedbackCreate(
            organization_id=entities[0].id,
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            customer_response="The timing is not right this month.",
            interest_level="medium",
            objection_category="timing",
            reason_lost="Budget timing",
            learning_signal="Beauty studios may prefer offers aligned to quieter booking periods.",
            confidence=0.78,
        ),
        entities[1].id,
    )
    assert feedback.learning_observation_id is None
    feedback = service.decide_feedback(feedback, "reviewed", entities[1].id)
    observation = ClosedLoopLearningService(db_session).create_observation(
        LearningObservationCreate(
            organization_id=entities[0].id,
            source_type="growth_customer_feedback",
            source_record_id=feedback.id,
            observation_type="approved_customer_feedback",
            observed_at=datetime.now(UTC),
            evidence_reference=f"growth_customer_feedback:{feedback.id}",
            confidence=feedback.confidence,
            metadata={"learning_signal": feedback.learning_signal},
        ),
        entities[1].id,
    )
    feedback = service.decide_feedback(feedback, "approved", entities[1].id, observation.id)
    observation = db_session.get(LearningObservation, feedback.learning_observation_id)
    assert observation is not None
    assert observation.source_type == "growth_customer_feedback"
    assert observation.source_record_id == feedback.id


def test_operations_dashboard_uses_finance_revenue_authority(db_session: Session) -> None:
    entities, _, _, _, payment, experiment, _ = operations_foundation(db_session, "dashboard")
    launch = RevenueLaunchService(db_session)
    # Use the experiment prospect's existing payment record with Finance truth.
    payment = launch.transition_payment(payment, "link_ready", None, entities[1].id)
    revenue = finance_observation(db_session, entities, "operations-dashboard")
    launch.transition_payment(payment, "paid_observed", revenue.id, entities[1].id)
    dashboard = RevenueOperationsService(db_session).dashboard(experiment.id, entities[0].id)
    assert dashboard.prospects_discovered == 1
    assert dashboard.qualified_prospects == 1
    assert dashboard.gifts_created == 1
    assert dashboard.offers == 1
    assert dashboard.paid_customers == 1
    assert dashboard.revenue == revenue.amount
    assert dashboard.revenue_currency == "USD"


def test_revenue_operations_api_requires_authentication(
    client: TestClient, db_session: Session
) -> None:
    entities, prospect, _, _, _, experiment, _ = operations_foundation(db_session, "api")
    response = client.post(
        "/api/v1/daily-experiment-workspace",
        json={
            "organization_id": str(entities[0].id),
            "workspace_date": "2026-08-22",
            "revenue_experiment_id": str(experiment.id),
            "prospect_id": str(prospect.id),
        },
    )
    assert response.status_code == 401
