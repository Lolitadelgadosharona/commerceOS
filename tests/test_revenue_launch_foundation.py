from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from commerce_os.finance.schemas import RevenueObservationCreate
from commerce_os.finance.services import FinanceIntelligenceService
from commerce_os.governance.models import AuditLog, Project
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_launch_models import CustomerLifecycleEvent
from commerce_os.growth.revenue_launch_schemas import (
    CustomerLifecycleEventCreate,
    PaymentReadinessCreate,
    RevenueOfferCreate,
    RevenuePipelineCreate,
)
from commerce_os.growth.revenue_launch_services import RevenueLaunchService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.test_revenue_experiment_execution import opportunity_and_gift


def launch_foundation(db_session: Session, suffix: str):
    entities, prospect, evidence, profile, pattern, recommendation, opportunity, gift = (
        opportunity_and_gift(db_session, suffix)
    )
    organization, user, *_ = entities
    service = RevenueLaunchService(db_session)
    pipeline = service.create_pipeline(
        RevenuePipelineCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            notes="Founder review started.",
        ),
        user.id,
    )
    offer = service.create_offer(
        RevenueOfferCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            offer_name="Beauty Visibility Package",
            price=Decimal("500.00"),
            currency="USD",
            scope="Homepage, GEO, and booking clarity improvements.",
        ),
        user.id,
    )
    offer = service.transition_offer(offer, "presented", "Proposal reviewed manually.", user.id)
    offer = service.transition_offer(offer, "accepted", "Customer accepted the scope.", user.id)
    payment = service.create_payment_readiness(
        PaymentReadinessCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            offer_tracking_id=offer.id,
            payment_provider_reference="provider-customer-reference",
            payment_link="https://payments.example/hosted-link-reference",
            invoice_reference="invoice-reference-001",
        ),
        user.id,
    )
    return entities, prospect, gift, pipeline, offer, payment, service


def finance_observation(db_session: Session, entities, suffix: str):  # type: ignore[no-untyped-def]
    organization = entities[0]
    project = Project(
        organization_id=organization.id,
        name=f"Revenue Launch {suffix}",
        slug=f"revenue-launch-{suffix}",
    )
    db_session.add(project)
    db_session.commit()
    return FinanceIntelligenceService(db_session).create_revenue(
        RevenueObservationCreate(
            organization_id=organization.id,
            project_id=project.id,
            channel="growthos",
            amount=Decimal("500.00"),
            currency="USD",
            source_type="manual",
            observation_date=date(2026, 8, 22),
        )
    )


def test_pipeline_is_ordered_and_every_transition_is_audited(db_session: Session) -> None:
    entities, _, gift, pipeline, _, _, service = launch_foundation(db_session, "pipeline")
    user = entities[1]
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_pipeline(pipeline, "gift_ready", "Skipped qualification.", user.id)
    pipeline = service.transition_pipeline(pipeline, "qualified", "Evidence reviewed.", user.id)
    pipeline = service.transition_pipeline(pipeline, "gift_ready", "Gift exists.", user.id)
    with pytest.raises(GrowthError, match="human-approved"):
        service.transition_pipeline(pipeline, "approved", "Not approved.", user.id)
    gift.status = "approved"
    db_session.commit()
    pipeline = service.transition_pipeline(
        pipeline, "approved", "Human approval observed.", user.id
    )
    audit = db_session.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_id == pipeline.id,
            AuditLog.action == "growthos.revenue_pipeline.transitioned",
        )
        .order_by(AuditLog.timestamp.desc())
    )
    assert pipeline.stage == "approved"
    assert audit is not None
    assert audit.event_metadata["to_stage"] == "approved"


def test_payment_status_requires_finance_truth(db_session: Session) -> None:
    entities, _, _, _, _, payment, service = launch_foundation(db_session, "payment")
    payment = service.transition_payment(payment, "link_ready", None, entities[1].id)
    with pytest.raises(GrowthError, match="Finance"):
        service.transition_payment(payment, "paid_observed", None, entities[1].id)
    revenue = finance_observation(db_session, entities, "payment")
    payment = service.transition_payment(payment, "paid_observed", revenue.id, entities[1].id)
    assert payment.revenue_observation_id == revenue.id


def test_customer_lifecycle_is_append_only_and_payment_backed(db_session: Session) -> None:
    entities, prospect, _, _, _, payment, service = launch_foundation(db_session, "lifecycle")
    with pytest.raises(GrowthError, match="Finance"):
        service.create_lifecycle_event(
            CustomerLifecycleEventCreate(
                organization_id=entities[0].id,
                prospect_id=prospect.id,
                lifecycle_type="first_purchase",
                source_reference="manual:purchase",
                occurred_at=datetime.now(UTC),
            ),
            entities[1].id,
        )
    payment = service.transition_payment(payment, "link_ready", None, entities[1].id)
    revenue = finance_observation(db_session, entities, "lifecycle")
    service.transition_payment(payment, "paid_observed", revenue.id, entities[1].id)
    event = service.create_lifecycle_event(
        CustomerLifecycleEventCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            lifecycle_type="first_purchase",
            source_reference=f"revenue:{revenue.id}",
            occurred_at=datetime.now(UTC),
            notes="Founder recorded purchase after Finance observation.",
        ),
        entities[1].id,
    )
    event.notes = "overwrite"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()
    assert isinstance(event, CustomerLifecycleEvent)


def test_command_center_uses_observed_pipeline_and_payment_records(db_session: Session) -> None:
    entities, _, _, pipeline, _, payment, service = launch_foundation(db_session, "dashboard")
    pipeline = service.transition_pipeline(
        pipeline, "qualified", "Evidence reviewed.", entities[1].id
    )
    payment = service.transition_payment(payment, "link_ready", None, entities[1].id)
    revenue = finance_observation(db_session, entities, "dashboard")
    service.transition_payment(payment, "paid_observed", revenue.id, entities[1].id)
    dashboard = service.command_center(entities[0].id, date(2026, 8, 22))
    assert dashboard.pipeline_by_stage["qualified"] == 1
    assert dashboard.paid_customers == 1
    assert dashboard.customer_replies == 0


def test_revenue_launch_api_requires_authentication(
    client: TestClient, db_session: Session
) -> None:
    entities, *_ = launch_foundation(db_session, "api")
    second = opportunity_and_gift(db_session, "api-second")[1]
    response = client.post(
        "/api/v1/revenue-pipelines",
        json={"organization_id": str(entities[0].id), "prospect_id": str(second.id)},
    )
    assert response.status_code == 401
