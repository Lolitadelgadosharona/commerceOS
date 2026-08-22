from datetime import UTC, datetime

import pytest
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_models import IndustryGrowthProfile
from commerce_os.growth.industry_intelligence_schemas import (
    GEOAssessmentCreate,
    IndustryEvidenceCreate,
    IndustryLearningSignalCreate,
    IndustryPatternCreate,
    IndustryProfileCreate,
    ServiceRecommendationCreate,
)
from commerce_os.growth.industry_intelligence_services import IndustryIntelligenceService
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_ai_research_operationalization import foundation
from tests.test_growthos_revenue_engine import prospect_and_evidence


def industry_foundation(db_session: Session, suffix: str = "industry"):
    entities = foundation(db_session, suffix)
    organization, user, *_ = entities
    prospect, prospect_evidence = prospect_and_evidence(db_session, entities)
    service = IndustryIntelligenceService(db_session)
    profile = service.create_profile(
        IndustryProfileCreate(
            organization_id=organization.id,
            industry_key=f"beauty-{suffix}",
            display_name="Beauty Services",
            vertical="beauty",
            scope_notes="Reusable local service-business scope; Beauty is the first profile.",
            confidence=0.8,
        ),
        user.id,
    )
    evidence = service.create_evidence(
        IndustryEvidenceCreate(
            organization_id=organization.id,
            industry_profile_id=profile.id,
            evidence_type="review_pattern",
            source_reference="controlled:review-set",
            observation="Customers repeatedly mention trust before booking.",
            confidence=0.84,
            captured_at=datetime.now(UTC),
        ),
        user.id,
    )
    return entities, prospect, prospect_evidence, profile, evidence, service


def test_reusable_industry_profile_and_evidence_pattern(db_session: Session) -> None:
    entities, _, _, profile, evidence, service = industry_foundation(db_session, "patterns")
    pattern = service.create_pattern(
        IndustryPatternCreate(
            organization_id=entities[0].id,
            industry_profile_id=profile.id,
            pattern_type="buying_trigger",
            title="Trust precedes booking",
            description="Review proof reduces uncertainty before a local service booking.",
            evidence_references=[evidence.id],
            confidence=0.79,
        ),
        entities[1].id,
    )
    assert profile.vertical == "beauty"
    assert pattern.evidence_references == [str(evidence.id)]


def test_geo_intelligence_is_evidence_backed_not_a_separate_engine(db_session: Session) -> None:
    entities, prospect, prospect_evidence, profile, _, service = industry_foundation(
        db_session, "geo"
    )
    geo = service.create_geo_assessment(
        GEOAssessmentCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            industry_profile_id=profile.id,
            website_signals={"entity_clarity": "weak", "location_signal": "observed"},
            social_signals={"profile_clarity": "unknown"},
            review_signals={"trust_language": "observed"},
            visibility_gaps=["Service entity is not explicit."],
            recommendations=["Clarify service, location, and FAQ relationships."],
            evidence_references=[prospect_evidence.id],
            confidence=0.74,
        ),
        entities[1].id,
    )
    assert geo.website_signals["entity_clarity"] == "weak"
    assert geo.evidence_references == [str(prospect_evidence.id)]


def test_service_recommendation_preserves_unknown_purchase_probability(db_session: Session) -> None:
    entities, prospect, prospect_evidence, profile, _, service = industry_foundation(
        db_session, "service"
    )
    recommendation = service.create_service_recommendation(
        ServiceRecommendationCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            industry_profile_id=profile.id,
            service_type="geo",
            customer_problem="The business entity is ambiguous to discovery systems.",
            recommended_scope="Clarify entity, service, location, FAQ, and expertise signals.",
            expected_value="Improved machine-readable business understanding; no outcome promise.",
            purchase_probability=None,
            quick_win_potential="high",
            evidence_references=[prospect_evidence.id],
            confidence=0.7,
        ),
        entities[1].id,
    )
    assert recommendation.purchase_probability is None
    assert recommendation.status == "draft"


def test_industry_learning_signal_retains_source_and_evidence(db_session: Session) -> None:
    entities, _, _, profile, evidence, service = industry_foundation(db_session, "learning")
    signal = service.create_learning_signal(
        IndustryLearningSignalCreate(
            organization_id=entities[0].id,
            industry_profile_id=profile.id,
            source_type="successful_offer",
            source_reference="growth-service:reviewed-outcome-1",
            pattern_type="service_outcome",
            observation="Review presentation was accepted as a useful quick win.",
            evidence_references=[evidence.id],
            confidence=0.76,
        ),
        entities[1].id,
    )
    assert signal.status == "draft"
    assert signal.source_reference == "growth-service:reviewed-outcome-1"


def test_industry_intelligence_rejects_cross_tenant_evidence(db_session: Session) -> None:
    entities, _, _, profile, _, service = industry_foundation(db_session, "tenant-a")
    other = industry_foundation(db_session, "tenant-b")
    with pytest.raises(GrowthError, match="this organization"):
        service.create_pattern(
            IndustryPatternCreate(
                organization_id=entities[0].id,
                industry_profile_id=profile.id,
                pattern_type="review",
                title="Unsafe cross-tenant pattern",
                description="Must fail.",
                evidence_references=[other[4].id],
                confidence=0.5,
            ),
            entities[1].id,
        )


def test_industry_api_requires_authenticated_actor(db_session: Session, client: TestClient) -> None:
    entities = foundation(db_session, "industry-api")
    organization, user, *_ = entities
    payload = IndustryProfileCreate(
        organization_id=organization.id,
        industry_key="pet",
        display_name="Pet Services",
        vertical="pet",
        scope_notes="Future vertical validates that Beauty is not hardcoded.",
        confidence=0.6,
    ).model_dump(mode="json")
    denied = client.post("/api/v1/industry-growth-profiles", json=payload)
    allowed = client.post(
        "/api/v1/industry-growth-profiles", json=payload, headers={"X-Actor-ID": str(user.id)}
    )
    assert denied.status_code == 401
    assert allowed.status_code == 201
    assert db_session.query(IndustryGrowthProfile).count() == 1
