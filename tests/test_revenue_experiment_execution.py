from datetime import date
from decimal import Decimal

import pytest
from commerce_os.finance.schemas import RevenueObservationCreate
from commerce_os.finance.services import FinanceIntelligenceService
from commerce_os.governance.models import Project
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_schemas import (
    IndustryPatternCreate,
    ServiceRecommendationCreate,
)
from commerce_os.growth.revenue_execution_schemas import DailyOpportunityCreate
from commerce_os.growth.revenue_execution_services import RevenueExecutionService
from commerce_os.growth.revenue_schemas import (
    AIModelPolicyCreate,
    GrowthGiftCreate,
    OpportunityAnalysisCreate,
    OutreachDraftCreate,
    SalesAnalysisCreate,
)
from commerce_os.growth.revenue_services import GrowthRevenueService
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_growthos_revenue_activation import approved_request
from tests.test_growthos_revenue_engine import completed_request
from tests.test_industry_intelligence_foundation import industry_foundation


def execution_foundation(db_session: Session, suffix: str):
    entities, prospect, prospect_evidence, profile, industry_evidence, industry = (
        industry_foundation(db_session, suffix)
    )
    organization, user, *_ = entities
    pattern = industry.create_pattern(
        IndustryPatternCreate(
            organization_id=organization.id,
            industry_profile_id=profile.id,
            pattern_type="geo",
            title="Weak entity clarity",
            description="Local service identity is difficult for discovery systems to understand.",
            evidence_references=[industry_evidence.id],
            confidence=0.78,
        ),
        user.id,
    )
    recommendation = industry.create_service_recommendation(
        ServiceRecommendationCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            industry_profile_id=profile.id,
            service_type="geo",
            customer_problem="Service identity and location relationship are unclear.",
            recommended_scope="Clarify entity, location, service, FAQ, and expertise signals.",
            expected_value="Improve AI visibility without promising placement or revenue.",
            purchase_probability=None,
            quick_win_potential="high",
            evidence_references=[prospect_evidence.id],
            confidence=0.73,
        ),
        user.id,
    )
    return entities, prospect, prospect_evidence, profile, pattern, recommendation


def opportunity_and_gift(db_session: Session, suffix: str):
    entities, prospect, evidence, profile, pattern, recommendation = execution_foundation(
        db_session, suffix
    )
    organization, user, *_ = entities
    revenue = GrowthRevenueService(db_session)
    opportunity = revenue.create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_type="seo",
            problem_statement="Local service identity is unclear.",
            evidence_reference=[evidence.id],
            customer_impact="Discovery systems may not connect service and location.",
            purchase_probability=None,
            confidence=0.75,
            recommended_offer="GEO clarity preview",
        ),
        user.id,
    )
    gift = revenue.create_gift(
        GrowthGiftCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_id=opportunity.id,
            title="AI visibility clarity preview",
            description="A customer-specific entity clarity example.",
            before_state="Service and location relationship is unclear.",
            after_state="Service, location, proof, and FAQ relationships are explicit.",
            evidence_reference=[evidence.id],
            gift_type="geo",
            before_asset_reference="artifact:before",
            after_asset_reference="artifact:after",
            customer_rationale="Prepared from this prospect's observed website evidence.",
        ),
        user.id,
    )
    return entities, prospect, evidence, profile, pattern, recommendation, opportunity, gift


def test_daily_queue_composes_existing_evidence_and_preserves_unknown_score(
    db_session: Session,
) -> None:
    entities, prospect, evidence, profile, pattern, recommendation = execution_foundation(
        db_session, "daily-queue"
    )
    queued = RevenueExecutionService(db_session).create_daily_opportunity(
        DailyOpportunityCreate(
            organization_id=entities[0].id,
            queue_date=date(2026, 8, 22),
            industry_profile_id=profile.id,
            prospect_id=prospect.id,
            evidence_references=[evidence.id],
            growth_pain="Weak local and AI discoverability.",
            industry_pattern_id=pattern.id,
            opportunity_score=None,
            service_recommendation_id=recommendation.id,
            confidence=0.72,
        ),
        entities[1].id,
    )
    assert queued.status == "review"
    assert queued.opportunity_score is None
    assert queued.evidence_references == [str(evidence.id)]


def test_growth_gift_pipeline_records_only_approved_human_execution(db_session: Session) -> None:
    entities, _, _, _, _, _, _, gift = opportunity_and_gift(db_session, "gift-pipeline")
    user = entities[1]
    revenue = GrowthRevenueService(db_session)
    gift = revenue.transition_gift(gift, "review", user.id, None)
    with pytest.raises(GrowthError, match="approval"):
        revenue.transition_gift(gift, "approved", user.id, None)
    approval = approved_request(
        db_session,
        entities,
        object_type="growth_gift",
        object_id=gift.id,
        action="approve_growth_gift",
    )
    gift = revenue.transition_gift(gift, "approved", user.id, approval.id)
    gift = revenue.transition_gift(gift, "sent", user.id, None)
    gift = revenue.transition_gift(
        gift, "customer_response", user.id, None, "This is specific and useful."
    )
    gift = revenue.transition_gift(gift, "converted", user.id, None)
    assert gift.status == "converted"
    assert gift.customer_response == "This is specific and useful."


def test_industry_aware_outreach_and_sales_copilot(db_session: Session) -> None:
    entities, prospect, evidence, profile, _, _, _, gift = opportunity_and_gift(
        db_session, "sales-copilot"
    )
    organization, user, *_ = entities
    gift.status = "approved"
    db_session.commit()
    revenue = GrowthRevenueService(db_session)
    draft_request = completed_request(db_session, entities, "draft")
    draft = revenue.create_outreach(
        OutreachDraftCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            growth_gift_id=gift.id,
            channel="email",
            subject="A specific visibility observation",
            body="I noticed a specific service clarity gap and prepared a useful example.",
            tone="helpful",
            evidence_used=[evidence.id],
            ai_request_id=draft_request.id,
            industry_profile_id=profile.id,
            industry_context="Beauty prospects often need service, proof, and booking clarity.",
            subject_options=["A specific visibility observation"],
            opening_sentence="I noticed the service and location relationship is hard to identify.",
            personalized_context="This is based on the supplied website observation.",
            problem_observation="The service entity is not explicit.",
            gift_explanation="I prepared a small clarity example.",
            soft_cta="Would it be useful if I shared it?",
        ),
        user.id,
    )
    analysis_request = completed_request(db_session, entities, "analysis")
    analysis = revenue.create_sales_analysis(
        SalesAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            conversation_reference="conversation:industry-aware",
            intent="question",
            sentiment="neutral",
            objection="We already have marketing.",
            buying_stage="considering",
            recommended_action="Focus on the specific missed visibility opportunity.",
            suggested_reply="Draft a narrow evidence-based clarification for human review.",
            ai_request_id=analysis_request.id,
            customer_reply="We already have marketing.",
            buying_signal="neutral",
            objection_type="existing_supplier",
            industry_profile_id=profile.id,
            industry_context="A common objection; avoid selling a generic marketing package.",
        ),
        user.id,
    )
    assert draft.industry_profile_id == profile.id
    assert analysis.industry_context.startswith("A common objection")


def test_outreach_rejects_generic_or_fake_claim_language(db_session: Session) -> None:
    entities, prospect, evidence, profile, _, _, _, gift = opportunity_and_gift(
        db_session, "outreach-safety"
    )
    gift.status = "approved"
    db_session.commit()
    request = completed_request(db_session, entities, "draft")
    with pytest.raises(GrowthError, match="not generic"):
        GrowthRevenueService(db_session).create_outreach(
            OutreachDraftCreate(
                organization_id=entities[0].id,
                prospect_id=prospect.id,
                growth_gift_id=gift.id,
                channel="email",
                body="We help businesses and guarantee results.",
                tone="aggressive",
                evidence_used=[evidence.id],
                ai_request_id=request.id,
                industry_profile_id=profile.id,
                industry_context="Beauty",
                subject_options=["Guaranteed results"],
                opening_sentence="We help businesses grow.",
                personalized_context="Generic pitch.",
                problem_observation="Generic.",
                gift_explanation="Generic.",
                soft_cta="Buy now.",
            ),
            entities[1].id,
        )


def test_revenue_dashboard_reads_finance_truth(db_session: Session) -> None:
    entities, prospect, *_ = execution_foundation(db_session, "dashboard")
    organization = entities[0]
    project = Project(
        organization_id=organization.id, name="GrowthOS Revenue", slug="growthos-revenue"
    )
    db_session.add(project)
    db_session.commit()
    finance = FinanceIntelligenceService(db_session)
    for source_type, amount in [("manual", "800"), ("manual", "200")]:
        finance.create_revenue(
            RevenueObservationCreate(
                organization_id=organization.id,
                project_id=project.id,
                channel="growthos",
                amount=Decimal(amount),
                currency="USD",
                source_type=source_type,
                observation_date=date(2026, 8, 22),
            )
        )
    prospect.status = "customer"
    db_session.commit()
    dashboard = RevenueExecutionService(db_session).dashboard(organization.id)
    assert dashboard.revenue == Decimal("1000")
    assert dashboard.mrr is None
    assert dashboard.ltv is None
    assert dashboard.customers_won == 1


def test_model_routing_is_provider_neutral_and_cost_governed(db_session: Session) -> None:
    entities = industry_foundation(db_session, "routing")[0]
    organization, user, *_ = entities
    service = GrowthRevenueService(db_session)
    policy = service.create_model_policy(
        AIModelPolicyCreate(
            organization_id=organization.id,
            task_type="opportunity_evaluation",
            provider_name="provider-registry-alias",
            preferred_model="quality-model-alias",
            fallback_model="economy-model-alias",
            quality_requirement="premium",
            cost_policy="capped",
            cost_limit=2.5,
        ),
        user.id,
    )
    assert policy.provider_name == "provider-registry-alias"
    with pytest.raises(GrowthError, match="cost limit"):
        service.create_model_policy(
            AIModelPolicyCreate(
                organization_id=organization.id,
                task_type="reply_drafting",
                preferred_model="quality-model-alias",
                quality_requirement="premium",
                cost_policy="capped",
            ),
            user.id,
        )


def test_revenue_execution_api_requires_authentication(
    db_session: Session, client: TestClient
) -> None:
    entities, prospect, evidence, profile, pattern, recommendation = execution_foundation(
        db_session, "api"
    )
    payload = DailyOpportunityCreate(
        organization_id=entities[0].id,
        queue_date=date(2026, 8, 22),
        industry_profile_id=profile.id,
        prospect_id=prospect.id,
        evidence_references=[evidence.id],
        growth_pain="AI visibility gap.",
        industry_pattern_id=pattern.id,
        service_recommendation_id=recommendation.id,
        confidence=0.7,
    ).model_dump(mode="json")
    assert client.post("/api/v1/daily-growth-opportunities", json=payload).status_code == 401
    allowed = client.post(
        "/api/v1/daily-growth-opportunities",
        json=payload,
        headers={"X-Actor-ID": str(entities[1].id)},
    )
    assert allowed.status_code == 201
