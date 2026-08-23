from datetime import date

import pytest
from commerce_os.governance.models import AuditLog
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.live_revenue_models import DailyRevenueRun, FounderActionItem
from commerce_os.growth.live_revenue_schemas import (
    CustomerDeliveryCreate,
    DailyRevenueRunCreate,
    DailyRunProspectAdd,
    DeliveryItemCreate,
    FounderActionCreate,
    GrowthConnectorCreate,
)
from commerce_os.growth.live_revenue_services import LiveRevenueService, scoped_live
from commerce_os.growth.revenue_launch_services import RevenueLaunchService
from commerce_os.growth.revenue_operations_schemas import (
    CustomerFeedbackCreate,
    WorkspaceItemCreate,
)
from commerce_os.growth.revenue_operations_services import RevenueOperationsService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.test_revenue_experiment_operations import operations_foundation
from tests.test_revenue_launch_foundation import finance_observation


def test_daily_run_requires_evidence_backed_assigned_prospect_and_audit(
    db_session: Session,
) -> None:
    entities, prospect, _, _, _, experiment, _ = operations_foundation(db_session, "run")
    service = LiveRevenueService(db_session)
    run = service.create_run(
        DailyRevenueRunCreate(
            organization_id=entities[0].id,
            revenue_experiment_id=experiment.id,
            run_date=date(2026, 8, 23),
            industry="Beauty",
            target_geography="Los Angeles, CA",
        ),
        entities[1].id,
    )
    with pytest.raises(GrowthError, match="at least one"):
        service.transition_run(run, "ready_for_review", entities[1].id)
    ranked = service.add_run_prospect(
        run,
        DailyRunProspectAdd(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            priority_rank=1,
            priority_score=88,
            evidence_reference=f"growth_prospect:{prospect.id}",
        ),
        entities[1].id,
    )
    run = service.transition_run(run, "ready_for_review", entities[1].id)
    run = service.transition_run(run, "approved", entities[1].id)
    audit = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == run.id,
            AuditLog.action == "growthos.daily_revenue_run.approved",
        )
    )
    assert ranked.priority_rank == 1
    assert run.generated_prospects == 1
    assert audit is not None


def test_founder_action_queue_supports_assignment_and_completion(db_session: Session) -> None:
    entities, prospect, gift, _, _, experiment, _ = operations_foundation(db_session, "action")
    workspace = RevenueOperationsService(db_session).create_workspace_item(
        WorkspaceItemCreate(
            organization_id=entities[0].id,
            workspace_date=date(2026, 8, 23),
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            growth_gift_id=gift.id,
            priority=90,
        ),
        entities[1].id,
    )
    service = LiveRevenueService(db_session)
    action = service.create_action(
        FounderActionCreate(
            organization_id=entities[0].id,
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            action_type="prospect_review",
            source_type="daily_workspace",
            source_reference_id=workspace.id,
            title="Review priority Beauty prospect",
            priority=90,
        ),
        entities[1].id,
    )
    action = service.decide_action(
        action, "assign", entities[1].id, "Founder owns review.", entities[1].id
    )
    action = service.decide_action(
        action, "complete", None, "Review completed manually.", entities[1].id
    )
    assert isinstance(action, FounderActionItem)
    assert action.status == "completed"
    assert action.completed_at is not None


def test_external_connector_is_metadata_only_policy_bound_and_secret_safe(
    db_session: Session,
) -> None:
    entities, *_ = operations_foundation(db_session, "connector")
    service = LiveRevenueService(db_session)
    with pytest.raises(GrowthError, match="credentials"):
        service.create_connector(
            GrowthConnectorCreate(
                organization_id=entities[0].id,
                name="Beauty Website Evidence",
                provider="provider-neutral",
                data_type="website",
                collection_mode="controlled_import",
                configuration={"api_key": "forbidden"},
                policy_reference="policy:public-data-only",
            ),
            entities[1].id,
        )
    connector = service.create_connector(
        GrowthConnectorCreate(
            organization_id=entities[0].id,
            name="Beauty Public Website Evidence",
            provider="provider-neutral",
            data_type="website",
            collection_mode="controlled_import",
            configuration={"allowed_fields": ["homepage", "services"]},
            policy_reference="policy:public-data-only",
        ),
        entities[1].id,
    )
    connector = service.transition_connector(connector, "configured", entities[1].id)
    connector = service.transition_connector(connector, "ready", entities[1].id)
    assert connector.status == "ready"


def test_paid_offer_delivery_requires_checklist_completion(db_session: Session) -> None:
    entities, prospect, _, offer, payment, _, _ = operations_foundation(db_session, "delivery")
    launch = RevenueLaunchService(db_session)
    payment = launch.transition_payment(payment, "link_ready", None, entities[1].id)
    revenue = finance_observation(db_session, entities, "live-delivery")
    launch.transition_payment(payment, "paid_observed", revenue.id, entities[1].id)
    service = LiveRevenueService(db_session)
    delivery = service.create_delivery(
        CustomerDeliveryCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            offer_tracking_id=offer.id,
        ),
        entities[1].id,
    )
    item = service.create_delivery_item(
        delivery,
        DeliveryItemCreate(
            organization_id=entities[0].id,
            item_type="milestone",
            title="Deliver approved GEO audit",
            description="Founder verifies the agreed deliverable.",
            sequence=1,
        ),
        entities[1].id,
    )
    delivery = service.transition_delivery(delivery, "in_progress", None, entities[1].id)
    with pytest.raises(GrowthError, match="all checklist"):
        service.transition_delivery(delivery, "completed", None, entities[1].id)
    service.transition_delivery_item(item, "completed", "delivery-proof:manual-1", entities[1].id)
    delivery = service.transition_delivery(
        delivery, "completed", "feedback:external-1", entities[1].id
    )
    assert delivery.completed_at is not None


def test_live_revenue_api_requires_authentication(client: TestClient, db_session: Session) -> None:
    entities, _, _, _, _, experiment, _ = operations_foundation(db_session, "api")
    response = client.post(
        "/api/v1/daily-revenue-runs",
        json={
            "organization_id": str(entities[0].id),
            "revenue_experiment_id": str(experiment.id),
            "run_date": "2026-08-23",
            "industry": "Beauty",
            "target_geography": "Los Angeles, CA",
        },
    )
    assert response.status_code == 401


def test_live_revenue_records_are_tenant_scoped(db_session: Session) -> None:
    first, _, _, _, _, experiment, _ = operations_foundation(db_session, "tenant-one")
    second, *_ = operations_foundation(db_session, "tenant-two")
    run = LiveRevenueService(db_session).create_run(
        DailyRevenueRunCreate(
            organization_id=first[0].id,
            revenue_experiment_id=experiment.id,
            run_date=date(2026, 8, 24),
            industry="Beauty",
            target_geography="Orange County, CA",
        ),
        first[1].id,
    )
    with pytest.raises(GrowthError, match="not found"):
        scoped_live(db_session, DailyRevenueRun, run.id, second[0].id)


def test_live_analytics_uses_reviewed_workspace_and_recorded_lost_reasons(
    db_session: Session,
) -> None:
    entities, prospect, gift, _, _, experiment, _ = operations_foundation(db_session, "metrics")
    operations = RevenueOperationsService(db_session)
    workspace = operations.create_workspace_item(
        WorkspaceItemCreate(
            organization_id=entities[0].id,
            workspace_date=date(2026, 8, 23),
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            growth_gift_id=gift.id,
            priority=75,
        ),
        entities[1].id,
    )
    operations.decide_workspace_item(workspace, "reject", "Not ready for this run.", entities[1].id)
    operations.create_feedback(
        CustomerFeedbackCreate(
            organization_id=entities[0].id,
            revenue_experiment_id=experiment.id,
            prospect_id=prospect.id,
            customer_response="We already have a supplier.",
            interest_level="low",
            objection_category="existing_supplier",
            reason_lost="existing supplier",
            learning_signal="Position around a specific gap instead of replacement.",
            confidence=0.8,
        ),
        entities[1].id,
    )
    metrics = LiveRevenueService(db_session).analytics(experiment.id, entities[0].id)
    assert metrics.prospects_reviewed == 1
    assert metrics.lost_reasons == {"existing supplier": 1}
