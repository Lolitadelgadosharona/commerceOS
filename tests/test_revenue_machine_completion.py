import pytest
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_schemas import (
    GrowthDiagnosisCreate,
    GrowthGiftCreate,
    IndustryDeliveryKnowledgeCreate,
    OfferRecommendationCreate,
    OpportunityAnalysisCreate,
    SalesAnalysisCreate,
)
from commerce_os.growth.revenue_services import GrowthRevenueService
from sqlalchemy.orm import Session

from tests.test_growthos_revenue_engine import completed_request
from tests.test_industry_intelligence_foundation import industry_foundation
from tests.test_revenue_experiment_execution import execution_foundation


def diagnosis_foundation(db_session: Session, suffix: str):
    entities, prospect, evidence, profile, _, _ = execution_foundation(db_session, suffix)
    organization, user, *_ = entities
    service = GrowthRevenueService(db_session)
    diagnosis = service.create_diagnosis(
        GrowthDiagnosisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            industry_profile_id=profile.id,
            business_situation="Independent beauty studio with observable local visibility gaps.",
            growth_problems=["The service and location relationship is unclear."],
            evidence_references=[evidence.id],
            customer_impact="Potential customers may struggle to confirm service fit.",
            recommended_improvements=["Clarify services, proof, location, and booking path."],
            confidence=0.76,
            risks=["Booking behavior has not been observed."],
        ),
        user.id,
    )
    return entities, prospect, evidence, profile, diagnosis, service


def test_diagnosis_requires_evidence_and_rejects_fake_promises(db_session: Session) -> None:
    entities, prospect, evidence, profile, _, service = diagnosis_foundation(
        db_session, "diagnosis"
    )
    with pytest.raises(GrowthError, match="unsupported"):
        service.create_diagnosis(
            GrowthDiagnosisCreate(
                organization_id=entities[0].id,
                prospect_id=prospect.id,
                industry_profile_id=profile.id,
                business_situation="Guaranteed revenue is available.",
                growth_problems=["Visibility is weak."],
                evidence_references=[evidence.id],
                customer_impact="Uncertain.",
                recommended_improvements=["Clarify the page."],
                confidence=0.5,
            ),
            entities[1].id,
        )


@pytest.mark.parametrize(
    ("stage", "locations", "visibility", "expected"),
    [
        ("new", 1, False, "launch_growth_package"),
        ("existing", 1, False, "growth_optimization_package"),
        ("existing", 2, False, "expansion_package"),
        ("existing", 1, True, "visibility_package"),
    ],
)
def test_offer_recommendation_is_deterministic_and_explainable(
    db_session: Session,
    stage: str,
    locations: int,
    visibility: bool,
    expected: str,
) -> None:
    entities, prospect, _, _, diagnosis, service = diagnosis_foundation(
        db_session, f"offer-{expected}"
    )
    offer = service.recommend_offer(
        OfferRecommendationCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            diagnosis_id=diagnosis.id,
            business_stage=stage,
            location_count=locations,
            high_review_weak_visibility=visibility,
            customer_fit="Matches the explicitly observed gap.",
            scope_summary="A narrow, human-reviewed improvement package.",
            confidence=0.72,
        ),
        entities[1].id,
    )
    assert offer.offer_type == expected
    assert offer.formula_version == "growth-offer-rules-v1"
    assert offer.rationale


def test_enhanced_gift_is_customer_specific_and_diagnosis_backed(db_session: Session) -> None:
    entities, prospect, evidence, _, diagnosis, service = diagnosis_foundation(db_session, "gift")
    opportunity = service.create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            opportunity_type="seo",
            problem_statement="Service and location relationship is unclear.",
            evidence_reference=[evidence.id],
            customer_impact="Customers may not confirm fit.",
            confidence=0.7,
            recommended_offer="Visibility preview",
        ),
        entities[1].id,
    )
    gift = service.create_gift(
        GrowthGiftCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            opportunity_id=opportunity.id,
            title="Beauty visibility preview",
            description="A prospect-specific improvement concept.",
            before_state="Service relationship is unclear.",
            after_state="Service, location, proof, and booking are explicit.",
            evidence_reference=[evidence.id],
            growth_diagnosis_id=diagnosis.id,
            personalized_diagnosis=diagnosis.business_situation,
            recommended_improvement="Clarify entity and booking signals.",
            implementation_scope="Homepage structure and FAQ outline.",
            customer_value_explanation="Reduce uncertainty before booking.",
        ),
        entities[1].id,
    )
    assert gift.growth_diagnosis_id == diagnosis.id
    assert gift.customer_value_explanation == "Reduce uncertainty before booking."


def test_reply_analysis_and_industry_knowledge_remain_advisory(db_session: Session) -> None:
    entities, prospect, _, profile, _, service = diagnosis_foundation(db_session, "learning")
    knowledge_entities, _, _, knowledge_profile, industry_evidence, _ = industry_foundation(
        db_session, "knowledge"
    )
    knowledge = GrowthRevenueService(db_session).create_delivery_knowledge(
        IndustryDeliveryKnowledgeCreate(
            organization_id=knowledge_entities[0].id,
            industry_profile_id=knowledge_profile.id,
            knowledge_type="geo",
            title="Beauty GEO playbook",
            content="Clarify service, location, proof, and FAQ relationships.",
            evidence_references=[industry_evidence.id],
            version_label="v1",
        ),
        knowledge_entities[1].id,
    )
    assert knowledge.status == "active"
    request = completed_request(db_session, entities, "analysis")
    analysis = service.create_sales_analysis(
        SalesAnalysisCreate(
            organization_id=entities[0].id,
            prospect_id=prospect.id,
            conversation_reference="reply:1",
            intent="price_objection",
            sentiment="neutral",
            objection="The price is higher than expected.",
            buying_stage="considering",
            recommended_action="Explain the narrow scope; do not discount automatically.",
            suggested_reply="Draft a concise scope explanation for human review.",
            ai_request_id=request.id,
            customer_reply="This costs more than I expected.",
            buying_signal="questioning",
            objection_type="price",
            industry_profile_id=profile.id,
            industry_context="Beauty service operators often compare against generic packages.",
            reply_classification="price_objection",
            response_risk="medium",
        ),
        entities[1].id,
    )
    assert analysis.reply_classification == "price_objection"
    assert analysis.status == "draft"
