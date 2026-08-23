from datetime import UTC, datetime

import pytest
from commerce_os.growth.discovery_models import ProspectMemoryEvent
from commerce_os.growth.discovery_schemas import (
    AutomationPlanCreate,
    DiscoverySourceCreate,
    GoogleBusinessResultCreate,
    ProspectMemoryEventCreate,
    QualificationInputs,
)
from commerce_os.growth.discovery_services import GrowthDiscoveryService
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_schemas import AIModelPolicyCreate
from commerce_os.growth.revenue_services import GrowthRevenueService
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_ai_research_operationalization import foundation
from tests.test_growthos_prospect_discovery import discovery_foundation


def automation_foundation(db_session: Session, suffix: str):  # type: ignore[no-untyped-def]
    entities = foundation(db_session, suffix)
    organization, user, *_ = entities
    service = GrowthDiscoveryService(db_session)
    source = service.create_source(
        DiscoverySourceCreate(
            organization_id=organization.id,
            source_type="google_business_profile",
            source_name=f"Google Business {suffix}",
            capability="controlled_public_business_discovery",
            adapter_key="growthos.google-business.v1",
            collection_mode="controlled_connector",
            metadata={"outreach": False, "fabricate_missing": False},
        ),
        user.id,
    )
    plan = service.create_automation_plan(
        AutomationPlanCreate(
            organization_id=organization.id,
            source_id=source.id,
            name=f"Daily Beauty discovery {suffix}",
            industry="beauty",
            geography="London",
            query_criteria={"segments": ["lash", "brow", "facial", "salon"]},
        ),
        user.id,
    )
    return entities, service, source, plan


def test_daily_discovery_lifecycle_and_results(db_session: Session) -> None:
    entities, service, source, plan = automation_foundation(db_session, "lifecycle")
    organization, user, *_ = entities
    run = service.start_automation_run(plan, user.id)
    assert run.status == "running"
    assert run.started_at is not None
    assert run.source_id == source.id
    result = service.record_google_business_result(
        GoogleBusinessResultCreate(
            organization_id=organization.id,
            discovery_run_id=run.id,
            external_reference="gbp:beauty-001",
            business_name="Controlled Lash Studio",
            category="Lash studio",
            location="London",
            rating=4.7,
            review_count=38,
            website="https://lash.example",
            public_profile={"opening_hours_observed": True},
            captured_at=datetime.now(UTC),
            confidence=0.91,
        ),
        user.id,
    )
    run = service.transition_run(run, "completed", user.id)
    assert result.candidate_id is not None
    assert run.result_count == 1
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_run(run, "running", user.id)


def test_google_business_missing_values_remain_unknown(db_session: Session) -> None:
    entities, service, _, plan = automation_foundation(db_session, "missing")
    organization, user, *_ = entities
    run = service.start_automation_run(plan, user.id)
    result = service.record_google_business_result(
        GoogleBusinessResultCreate(
            organization_id=organization.id,
            discovery_run_id=run.id,
            external_reference="gbp:unknowns",
            business_name="Unknown Review Studio",
            category="Beauty salon",
            location="London",
            rating=None,
            review_count=None,
            website=None,
            captured_at=datetime.now(UTC),
            confidence=0.6,
        ),
        user.id,
    )
    assert result.rating is None
    assert result.review_count is None
    assert result.website is None


def test_ranked_prospects_reuse_qualification_formula(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "daily-ranking")
    organization, user, *_ = entities
    service.qualify(
        candidate,
        QualificationInputs(
            organization_id=organization.id,
            pain_signal=90,
            purchase_probability=70,
            accessibility=80,
            quick_win_potential=100,
        ),
        user.id,
    )
    ranked = service.ranked_prospects(organization.id)
    assert ranked[0].candidate_id == candidate.id
    assert ranked[0].score == 83.5
    assert ranked[0].growth_pain == 90


def test_prospect_memory_is_append_only_and_requires_change(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "memory")
    organization, user, *_ = entities
    source = service.create_source(
        DiscoverySourceCreate(
            organization_id=organization.id,
            source_type="website",
            source_name="Website memory",
            capability="controlled_change_observation",
            adapter_key="growthos.website.v1",
            collection_mode="controlled_import",
        ),
        user.id,
    )
    payload = ProspectMemoryEventCreate(
        organization_id=organization.id,
        candidate_id=candidate.id,
        source_id=source.id,
        change_type="website_update",
        source_reference="https://beauty.example",
        previous_state={"booking_visible": False},
        observed_state={"booking_visible": True},
        observed_at=datetime.now(UTC),
        confidence=0.86,
    )
    event = service.record_memory_event(payload, user.id)
    event.observed_state = {"unsupported": True}
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    assert db_session.query(ProspectMemoryEvent).count() == 1
    with pytest.raises(GrowthError, match="observed change"):
        service.record_memory_event(
            payload.model_copy(update={"observed_state": payload.previous_state}), user.id
        )


def test_ai_routing_remains_provider_neutral(db_session: Session) -> None:
    entities = foundation(db_session, "automation-routing")
    organization, user, *_ = entities
    service = GrowthRevenueService(db_session)
    discovery = service.create_model_policy(
        AIModelPolicyCreate(
            organization_id=organization.id,
            task_type="prospect_research",
            preferred_model="economy-discovery-alias",
            fallback_model="economy-fallback-alias",
            quality_requirement="economy",
            provider_name="registry-selected",
            cost_policy="lowest_cost",
        ),
        user.id,
    )
    reasoning = service.create_model_policy(
        AIModelPolicyCreate(
            organization_id=organization.id,
            task_type="opportunity_evaluation",
            preferred_model="quality-reasoning-alias",
            quality_requirement="premium",
            provider_name="registry-selected",
            cost_policy="quality_first",
        ),
        user.id,
    )
    assert discovery.cost_policy == "lowest_cost"
    assert reasoning.quality_requirement == "premium"


def test_automation_api_requires_authentication(db_session: Session, client: TestClient) -> None:
    entities, _, _, plan = automation_foundation(db_session, "api")
    organization, user, *_ = entities
    path = f"/api/v1/discovery-automation-plans/{plan.id}/runs"
    client.app.state.auth_test_bypass = False  # type: ignore[attr-defined]
    denied = client.post(path, params={"organization_id": organization.id})
    client.app.state.auth_test_bypass = True  # type: ignore[attr-defined]
    allowed = client.post(
        path,
        params={"organization_id": organization.id},
        headers={"X-Actor-ID": str(user.id)},
    )
    assert denied.status_code == 401
    assert allowed.status_code == 201
