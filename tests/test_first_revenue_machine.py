from datetime import UTC, datetime
from decimal import Decimal

import pytest
from commerce_os.ai_runtime.models import AICostObservation
from commerce_os.growth.activation_schemas import RevenueExperimentCreate
from commerce_os.growth.activation_services import RevenueActivationService
from commerce_os.growth.discovery_schemas import (
    BusinessProfileEvidenceCreate,
    DiscoverySourceCreate,
    InstagramEvidenceCreate,
    QualificationInputs,
    WebsiteEvidenceCreate,
)
from commerce_os.growth.discovery_services import GrowthDiscoveryService
from commerce_os.growth.errors import GrowthError
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_growthos_prospect_discovery import discovery_foundation


def source_for(
    db_session: Session,
    entities,
    source_type: str,
    suffix: str,  # type: ignore[no-untyped-def]
):
    organization, user, *_ = entities
    return GrowthDiscoveryService(db_session).create_source(
        DiscoverySourceCreate(
            organization_id=organization.id,
            source_type=source_type,  # type: ignore[arg-type]
            source_name=f"{source_type}-{suffix}",
            capability="structured_evidence_import",
            adapter_key=f"growthos.{source_type}.v1",
            collection_mode="controlled_import",
            metadata={"network_execution": False},
        ),
        user.id,
    )


def test_source_adapter_contract_is_provider_neutral(db_session: Session) -> None:
    entities, *_ = discovery_foundation(db_session, "adapter")
    for source_type in [
        "website",
        "google_business_profile",
        "instagram",
        "manual",
        "tiktok",
        "reddit",
        "yelp",
        "google_trends",
        "news",
        "other",
    ]:
        source = source_for(db_session, entities, source_type, "adapter")
        assert source.collection_mode == "controlled_import"
        assert source.source_metadata["network_execution"] is False


def test_structured_evidence_collectors_preserve_provenance(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "collectors")
    organization, user, *_ = entities
    captured = datetime.now(UTC)
    website = source_for(db_session, entities, "website", "collectors")
    profile = source_for(db_session, entities, "google_business_profile", "collectors")
    instagram = source_for(db_session, entities, "instagram", "collectors")
    website_evidence = service.collect_website_evidence(
        WebsiteEvidenceCreate(
            organization_id=organization.id,
            candidate_id=candidate.id,
            source_id=website.id,
            source_url="https://beauty.example",
            business_name="Evidence Beauty Studio",
            location="London",
            services=["lash extensions", "brow styling"],
            website_structure={"service_pages": True},
            homepage_signals={"positioning": "unclear"},
            booking_flow_signals={"above_fold_booking": False},
            seo_signals={"title_observed": True},
            geo_visibility_signals={"service_location_relationship": "weak"},
            captured_at=captured,
            confidence=0.88,
        ),
        user.id,
    )
    service.collect_business_profile_evidence(
        BusinessProfileEvidenceCreate(
            organization_id=organization.id,
            candidate_id=candidate.id,
            source_id=profile.id,
            source_reference="gbp:controlled-reference",
            review_count=42,
            rating=4.6,
            location="London",
            business_category="Beauty salon",
            customer_language=["gentle", "easy booking"],
            captured_at=captured,
            confidence=0.9,
        ),
        user.id,
    )
    service.collect_instagram_evidence(
        InstagramEvidenceCreate(
            organization_id=organization.id,
            candidate_id=candidate.id,
            source_id=instagram.id,
            profile_reference="instagram:controlled-reference",
            profile_information={"bio_observed": True},
            posting_frequency="observed weekly",
            content_themes=["before and after", "client education"],
            brand_signals={"visual_consistency": "medium"},
            captured_at=captured,
            confidence=0.76,
        ),
        user.id,
    )
    assert website_evidence.source_id == website.id
    assert service.pipeline(candidate.id, organization.id).evidence_count == 4
    website_evidence.business_name = "Unsupported overwrite"
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()


def test_collector_rejects_wrong_source_and_cross_tenant(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "collector-boundary")
    wrong = source_for(db_session, entities, "instagram", "wrong")
    other = discovery_foundation(db_session, "collector-other")[0]
    payload = WebsiteEvidenceCreate(
        organization_id=entities[0].id,
        candidate_id=candidate.id,
        source_id=wrong.id,
        source_url="https://beauty.example",
        business_name="Beauty",
        captured_at=datetime.now(UTC),
        confidence=0.7,
    )
    with pytest.raises(GrowthError, match="source type"):
        service.collect_website_evidence(payload, entities[1].id)
    with pytest.raises(GrowthError, match="this organization"):
        GrowthDiscoveryService(db_session).pipeline(candidate.id, other[0].id)


def test_prospect_pipeline_exposes_next_human_work(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "pipeline")
    organization, user, *_ = entities
    assert service.pipeline(candidate.id, organization.id).next_step == "qualify_prospect"
    service.qualify(
        candidate,
        QualificationInputs(
            organization_id=organization.id,
            pain_signal=85,
            purchase_probability=70,
            accessibility=90,
            quick_win_potential=90,
        ),
        user.id,
    )
    assert service.pipeline(candidate.id, organization.id).next_step == "activate_prospect"


def test_operator_dashboard_reports_business_activity_and_cost(db_session: Session) -> None:
    entities, service, _, candidate, *_ = discovery_foundation(db_session, "operator-dashboard")
    organization, user, _, provider, capability, _ = entities
    RevenueActivationService(db_session).create_experiment(
        RevenueExperimentCreate(
            organization_id=organization.id,
            name="Beauty Growth Experiment #001",
            description="Founder-operated validation.",
            target_segment="Independent Beauty studios",
            offer_type="growth_visibility_audit",
            message_strategy="Evidence first",
        ),
        user.id,
    )
    db_session.add(
        AICostObservation(
            organization_id=organization.id,
            provider_id=provider.id,
            capability_id=capability.id,
            usage_quantity=Decimal("500"),
            usage_unit="tokens",
            estimated_cost=Decimal("0.05"),
            currency="USD",
            project_id=None,
            related_request_id=None,
            cost_basis="estimated",
        )
    )
    db_session.commit()
    dashboard = service.operator_dashboard(organization.id)
    assert dashboard.daily_prospects_discovered == 1
    assert dashboard.revenue_experiments == 1
    assert dashboard.estimated_ai_cost == 0.05
    assert candidate.business_name == "Evidence Beauty Studio"


def test_operator_endpoints_require_authentication(db_session: Session, client: TestClient) -> None:
    entities, _, _, candidate, *_ = discovery_foundation(db_session, "operator-api")
    organization, user, *_ = entities
    path = f"/api/v1/prospect-candidates/{candidate.id}/pipeline"
    client.app.state.auth_test_bypass = False  # type: ignore[attr-defined]
    denied = client.get(path, params={"organization_id": organization.id})
    client.app.state.auth_test_bypass = True  # type: ignore[attr-defined]
    allowed = client.get(
        path,
        params={"organization_id": organization.id},
        headers={"X-Actor-ID": str(user.id)},
    )
    assert denied.status_code == 401
    assert allowed.status_code == 200
