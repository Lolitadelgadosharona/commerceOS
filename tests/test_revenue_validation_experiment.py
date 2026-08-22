from datetime import date
from decimal import Decimal

import pytest
from commerce_os.ai_runtime.models import AICostObservation
from commerce_os.finance.schemas import RevenueObservationCreate
from commerce_os.finance.services import FinanceIntelligenceService
from commerce_os.governance.models import Project
from commerce_os.growth.activation_schemas import (
    FeedbackSignalCreate,
    OfferExperimentCreate,
    OfferOutcomeCreate,
    ProspectAssignmentCreate,
    RevenueExperimentCreate,
)
from commerce_os.growth.activation_services import RevenueActivationService
from commerce_os.growth.discovery_schemas import DiscoverySourceCreate
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_schemas import IndustryLearningSignalCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import app
from tests.test_growthos_revenue_engine import completed_request
from tests.test_industry_intelligence_foundation import industry_foundation


def validation_experiment(db_session: Session, suffix: str):  # type: ignore[no-untyped-def]
    entities, prospect, _, profile, evidence, industry = industry_foundation(db_session, suffix)
    organization, user, *_ = entities
    experiment = RevenueActivationService(db_session).create_experiment(
        RevenueExperimentCreate(
            organization_id=organization.id,
            name="Beauty Growth Experiment #001",
            description="Governed validation for independent Beauty businesses.",
            target_segment="Lash, brow, facial studios and small salons",
            offer_type="multi_offer",
            message_strategy="Specific evidence and a useful Growth Gift.",
            industry_profile_id=profile.id,
            segment="independent_beauty",
            target_count=40,
            start_date=date(2026, 8, 22),
            success_metrics={"positive_reply_rate": 0.1, "customer_count": 2},
        ),
        user.id,
    )
    return entities, prospect, profile, evidence, industry, experiment


def test_experiment_lifecycle_and_beauty_scope(db_session: Session) -> None:
    entities, _, profile, _, _, experiment = validation_experiment(db_session, "validation")
    service = RevenueActivationService(db_session)
    assert experiment.industry_profile_id == profile.id
    assert experiment.target_count == 40
    for status in ["active", "paused", "active", "completed"]:
        experiment = service.transition_experiment(experiment, status, entities[1].id)
    with pytest.raises(GrowthError, match="cannot transition"):
        service.transition_experiment(experiment, "active", entities[1].id)


def test_offer_measurement_uses_finance_truth(db_session: Session) -> None:
    entities, prospect, _, _, _, experiment = validation_experiment(db_session, "offers")
    organization, user, *_ = entities
    service = RevenueActivationService(db_session)
    offer = service.create_offer_experiment(
        OfferExperimentCreate(
            organization_id=organization.id,
            revenue_experiment_id=experiment.id,
            offer_type="geo_optimization",
            prospect_segment="lash_studios",
            hypothesis="A specific GEO review earns more replies than a generic offer.",
        ),
        user.id,
    )
    project = Project(organization_id=organization.id, name="Validation", slug="validation")
    db_session.add(project)
    db_session.commit()
    revenue = FinanceIntelligenceService(db_session).create_revenue(
        RevenueObservationCreate(
            organization_id=organization.id,
            project_id=project.id,
            channel="growthos",
            amount=Decimal("450"),
            currency="USD",
            source_type="manual",
            observation_date=date(2026, 8, 22),
        )
    )
    service.record_offer_outcome(
        OfferOutcomeCreate(
            organization_id=organization.id,
            offer_experiment_id=offer.id,
            prospect_id=prospect.id,
            outreach_sent=True,
            replied=True,
            positive_reply=True,
            converted=True,
            revenue_observation_id=revenue.id,
        ),
        user.id,
    )
    dashboard = service.experiment_dashboard(experiment.id, organization.id)
    assert dashboard.offers[0].response_rate == 1
    assert dashboard.offers[0].conversion_rate == 1
    assert dashboard.revenue == Decimal("450")
    assert dashboard.currency == "USD"


def test_feedback_reuses_industry_learning_loop(db_session: Session) -> None:
    entities, _, profile, evidence, industry, experiment = validation_experiment(
        db_session, "feedback"
    )
    organization, user, *_ = entities
    learning = industry.create_learning_signal(
        IndustryLearningSignalCreate(
            organization_id=organization.id,
            industry_profile_id=profile.id,
            source_type="objection",
            source_reference="conversation:reviewed-1",
            pattern_type="objection",
            observation="Prospects ask for proof before accepting a visibility offer.",
            evidence_references=[evidence.id],
            confidence=0.75,
        ),
        user.id,
    )
    signal = RevenueActivationService(db_session).create_feedback_signal(
        FeedbackSignalCreate(
            organization_id=organization.id,
            revenue_experiment_id=experiment.id,
            source_type="objection",
            source_reference="conversation:reviewed-1",
            objection_category="trust",
            frequency=3,
            industry="beauty",
            recommended_response="Use reviewed evidence and ask a narrow follow-up question.",
            learning_signal="Lead with business-specific proof, not a broad marketing pitch.",
            industry_learning_signal_id=learning.id,
        ),
        user.id,
    )
    assert signal.frequency == 3
    assert signal.industry_learning_signal_id == learning.id


def test_funnel_and_ai_cost_are_experiment_scoped(db_session: Session) -> None:
    entities, prospect, _, _, _, experiment = validation_experiment(db_session, "funnel")
    organization, user, _, provider, capability, _ = entities
    prospect.status = "qualified"
    db_session.commit()
    RevenueActivationService(db_session).assign_prospect(
        ProspectAssignmentCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            prospect_id=prospect.id,
            assigned_offer="Growth Visibility Audit",
            assigned_message="Evidence-specific draft for human review.",
        ),
        user.id,
    )
    request = completed_request(db_session, entities, "analysis")
    request.context_type = "revenue_experiment"
    request.context_reference = str(experiment.id)
    db_session.add(
        AICostObservation(
            organization_id=organization.id,
            provider_id=provider.id,
            capability_id=capability.id,
            usage_quantity=Decimal("1000"),
            usage_unit="tokens",
            estimated_cost=Decimal("0.125"),
            currency="USD",
            project_id=None,
            related_request_id=request.id,
            cost_basis="estimated",
        )
    )
    db_session.commit()
    dashboard = RevenueActivationService(db_session).experiment_dashboard(
        experiment.id, organization.id
    )
    assert dashboard.funnel[0].count == 1
    assert dashboard.funnel[1].count == 1
    assert dashboard.estimated_ai_cost == Decimal("0.125")


@pytest.mark.parametrize(
    "source_type",
    ["website", "google_business_profile", "reviews", "instagram", "tiktok", "reddit"],
)
def test_external_discovery_sources_are_contracts_only(source_type: str) -> None:
    payload = DiscoverySourceCreate(
        organization_id="00000000-0000-0000-0000-000000000001",
        source_type=source_type,  # type: ignore[arg-type]
        source_name=f"Future {source_type}",
        capability="metadata_contract_only",
        metadata={"external_calls": False},
    )
    assert payload.metadata["external_calls"] is False


def test_revenue_validation_api_requires_authentication(
    db_session: Session, client: TestClient
) -> None:
    entities, _, _, _, _, experiment = validation_experiment(db_session, "api")
    organization, user, *_ = entities
    path = f"/api/v1/revenue-experiments/{experiment.id}/dashboard"
    app.state.auth_test_bypass = False
    denied = client.get(path, params={"organization_id": organization.id})
    app.state.auth_test_bypass = True
    allowed = client.get(
        path,
        params={"organization_id": organization.id},
        headers={"X-Actor-ID": str(user.id)},
    )
    assert denied.status_code == 401
    assert allowed.status_code == 200
