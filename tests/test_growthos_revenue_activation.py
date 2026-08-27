from datetime import UTC, datetime
from uuid import uuid4

import pytest
from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalStatus, Permission, Role
from commerce_os.governance.rbac import RbacService
from commerce_os.growth.activation_models import OutreachTrackingEvent
from commerce_os.growth.activation_schemas import (
    OutreachEventCreate,
    ProspectAssignmentCreate,
    ProspectPromotionCreate,
    RevenueExperimentCreate,
)
from commerce_os.growth.activation_services import RevenueActivationService, scoped_activation
from commerce_os.growth.discovery_models import ProspectCandidate
from commerce_os.growth.discovery_schemas import QualificationInputs
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import GrowthGift, GrowthOutreachDraft, GrowthProspect
from commerce_os.growth.revenue_schemas import (
    GrowthGiftCreate,
    GrowthPackagePreparationCreate,
    OpportunityAnalysisCreate,
    OutreachDraftCreate,
    ProspectEvidenceCreate,
    SalesAnalysisCreate,
)
from commerce_os.growth.revenue_services import GrowthRevenueService
from sqlalchemy.orm import Session

from tests.test_growthos_prospect_discovery import discovery_foundation
from tests.test_growthos_revenue_engine import completed_request

PASSWORD = "correct horse battery staple"

PACKAGE_RESPONSE = {
    "business_situation": "The public booking path is present but lightly explained.",
    "pain_points": ["Booking trust information is limited."],
    "customer_impact": "Prospective customers may hesitate before booking.",
    "recommended_improvements": ["Add a concise trust and booking explainer."],
    "opportunity_type": "website_conversion",
    "recommended_offer": "Booking Trust Preview",
    "risks": ["No conversion analytics are available."],
    "missing_information": ["Booking conversion rate"],
    "confidence": 0.78,
    "gift": {
        "title": "Booking Trust Preview",
        "description": "A customer-safe preview based on the public booking page.",
        "before_state": "Booking details are dispersed.",
        "after_state": "A concise trust block explains the next step.",
        "recommended_improvement": "Add a trust block beside the booking action.",
        "expected_value": "Reduce uncertainty without promising results.",
        "customer_rationale": "The preview is specific to the observed public flow.",
        "implementation_scope": "One booking trust block.",
        "customer_value_explanation": "Makes the next step easier to understand.",
    },
    "email": {
        "subject": "A booking-page idea for your studio",
        "body": "I noticed one specific booking-page opportunity and made a small preview.",
        "opening_sentence": "I noticed one specific detail on your booking page.",
        "personalized_context": "The public page has a clear booking action.",
        "problem_observation": "Trust details are separated from that action.",
        "gift_explanation": "I made a concise before/after preview.",
        "soft_cta": "Would it be useful if I sent it over?",
    },
}


def approved_request(
    session: Session,
    entities,  # type: ignore[no-untyped-def]
    *,
    object_type: str,
    object_id,  # type: ignore[no-untyped-def]
    action: str,
):  # type: ignore[no-untyped-def]
    organization, requester, *_ = entities
    approver = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"approver-{object_id}@example.test",
        display_name="Human Approver",
        password=PASSWORD,
    )
    role = Role(
        organization_id=organization.id,
        name=f"approver-{object_id}",
        grants_human_approval_authority=True,
    )
    permission = session.query(Permission).filter_by(key="approval.decide").one_or_none()
    if permission is None:
        permission = Permission(
            key="approval.decide",
            resource="approval",
            action="decide",
            is_human_approval_permission=True,
        )
    session.add_all([role, permission])
    session.commit()
    rbac = RbacService(session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=requester.id)
    rbac.assign_role(
        user_id=approver.id,
        role_id=role.id,
        organization_id=organization.id,
        project_id=None,
        assigned_by=requester.id,
    )
    workflow = ApprovalWorkflowService(session)
    approval = workflow.request(
        organization_id=organization.id,
        project_id=None,
        requester_id=requester.id,
        object_type=object_type,
        object_id=object_id,
        requested_action=action,
        reason="Human review required by GrowthOS governance.",
    )
    return workflow.decide(
        approval_id=approval.id,
        approver_id=approver.id,
        decision=ApprovalStatus.APPROVED,
        reason="Evidence and authority boundary reviewed.",
    )


def qualified_activation_foundation(session: Session, slug: str):  # type: ignore[no-untyped-def]
    entities, discovery, _, candidate, discovery_evidence, _ = discovery_foundation(session, slug)
    organization, user, *_ = entities
    discovery.qualify(
        candidate,
        QualificationInputs(
            organization_id=organization.id,
            pain_signal=85,
            purchase_probability=75,
            accessibility=90,
            quick_win_potential=90,
        ),
        user.id,
    )
    activation = RevenueActivationService(session)
    prospect = activation.promote_candidate(
        candidate,
        ProspectPromotionCreate(
            organization_id=organization.id,
            email="founder@beauty.example",
            social_links={"linkedin": "business:beauty"},
        ),
        user.id,
    )
    revenue = GrowthRevenueService(session)
    evidence = revenue.create_evidence(
        ProspectEvidenceCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            evidence_type=discovery_evidence.evidence_type,
            source_url=discovery_evidence.source_url,
            observation=discovery_evidence.observation,
            confidence=discovery_evidence.confidence,
            collected_at=discovery_evidence.collected_at,
        ),
        user.id,
    )
    return entities, activation, revenue, prospect, evidence


def test_revenue_experiment_and_candidate_promotion_are_controlled(db_session: Session) -> None:
    entities, activation, _, prospect, _ = qualified_activation_foundation(
        db_session, "activation-lifecycle"
    )
    organization, user, *_ = entities
    assert prospect.source_candidate_id is not None and prospect.status == "qualified"
    duplicate = activation.promote_candidate(
        db_session.get(ProspectCandidate, prospect.source_candidate_id),
        ProspectPromotionCreate(organization_id=organization.id),
        user.id,
    )
    assert duplicate.id == prospect.id
    experiment = activation.create_experiment(
        RevenueExperimentCreate(
            organization_id=organization.id,
            name="Founder evidence outreach",
            description="Validate one evidence-backed offer.",
            target_segment="Independent beauty studios",
            offer_type="growth_gift",
            message_strategy="Specific observation and a soft invitation.",
        ),
        user.id,
    )
    link = activation.assign_prospect(
        ProspectAssignmentCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            prospect_id=prospect.id,
            assigned_offer="Homepage clarity preview",
            assigned_message="Evidence-led founder outreach",
        ),
        user.id,
    )
    assert link.result_status == "pending"
    experiment = activation.transition_experiment(experiment, "active", user.id)
    experiment = activation.transition_experiment(experiment, "completed", user.id)
    with pytest.raises(GrowthError, match="cannot transition"):
        activation.transition_experiment(experiment, "active", user.id)


def test_growth_package_preparation_creates_review_only_artifacts(db_session: Session) -> None:
    entities, _, revenue, prospect, _ = qualified_activation_foundation(
        db_session, "package-preparation"
    )
    organization, user, _, provider, capability, _ = entities
    result = revenue.prepare_growth_package(
        GrowthPackagePreparationCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            capability_id=capability.id,
        ),
        user.id,
        {provider.provider_identity: DeterministicProviderAdapter(PACKAGE_RESPONSE)},
    )
    gift = db_session.get(GrowthGift, result.growth_gift_id)
    draft = db_session.get(GrowthOutreachDraft, result.outreach_draft_id)
    assert gift is not None and gift.status == "draft"
    assert draft is not None and draft.status == "draft"
    assert gift.approval_request_id is None and draft.approval_request_id is None


def test_growth_gift_outreach_and_sales_copilot_require_human_authority(
    db_session: Session,
) -> None:
    entities, activation, revenue, prospect, evidence = qualified_activation_foundation(
        db_session, "activation-authority"
    )
    organization, user, *_ = entities
    analysis_request = completed_request(db_session, entities, "analysis")
    opportunity = revenue.create_opportunity(
        OpportunityAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_type="booking_experience_fix",
            problem_statement="The booking path is difficult to locate.",
            evidence_reference=[evidence.id],
            customer_impact="Qualified visitors may abandon.",
            confidence=0.84,
            recommended_offer="Homepage clarity preview",
            ai_request_id=analysis_request.id,
        ),
        user.id,
    )
    gift = revenue.create_gift(
        GrowthGiftCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            opportunity_id=opportunity.id,
            title="Homepage clarity preview",
            description="A small evidence-backed improvement preview.",
            before_state="Booking path is hard to locate.",
            after_state="Booking path is visible and specific.",
            evidence_reference=[evidence.id],
        ),
        user.id,
    )
    gift = revenue.transition_gift(gift, "review", user.id, None)
    with pytest.raises(GrowthError, match="approval"):
        revenue.transition_gift(gift, "approved", user.id, None)
    gift_approval = approved_request(
        db_session,
        entities,
        object_type="growth_gift",
        object_id=gift.id,
        action="approve_growth_gift",
    )
    gift = revenue.transition_gift(gift, "approved", user.id, gift_approval.id)
    gift = revenue.transition_gift(gift, "ready_for_delivery", user.id, None)
    gift = revenue.transition_gift(gift, "delivered", user.id, None)

    draft_request = completed_request(db_session, entities, "draft")
    payload = OutreachDraftCreate(
        organization_id=organization.id,
        prospect_id=prospect.id,
        growth_gift_id=gift.id,
        channel="email",
        subject="A booking-path observation",
        body="I prepared a small homepage preview based on the visible booking path.",
        tone="founder_to_founder",
        evidence_used=[evidence.id],
        ai_request_id=draft_request.id,
        subject_options=["A booking-path observation", "Small homepage preview"],
        opening_sentence="I noticed the booking action is difficult to find on the homepage.",
        personalized_context="This is based on the supplied homepage observation.",
        problem_observation="The main booking action is not visible in the initial view.",
        gift_explanation="I prepared a small clarity preview to make the path concrete.",
        soft_cta="Would it be useful if I shared the preview?",
    )
    draft = revenue.create_outreach(payload, user.id)
    draft = revenue.transition_outreach(draft, "human_review", user.id, None)
    outreach_approval = approved_request(
        db_session,
        entities,
        object_type="growth_outreach_draft",
        object_id=draft.id,
        action="approve_outreach",
    )
    draft = revenue.transition_outreach(draft, "approved", user.id, outreach_approval.id)
    draft = revenue.transition_outreach(draft, "sent", user.id, None)

    experiment = activation.create_experiment(
        RevenueExperimentCreate(
            organization_id=organization.id,
            name="Booking clarity",
            description="Test the evidence-backed gift.",
            target_segment="Beauty studios",
            offer_type="growth_gift",
            message_strategy="Specific and low pressure.",
        ),
        user.id,
    )
    link = activation.assign_prospect(
        ProspectAssignmentCreate(
            organization_id=organization.id,
            experiment_id=experiment.id,
            prospect_id=prospect.id,
            assigned_offer="Homepage clarity preview",
            assigned_message="Observation plus gift",
        ),
        user.id,
    )
    sent = activation.record_event(
        OutreachEventCreate(
            organization_id=organization.id,
            prospect_experiment_link_id=link.id,
            outreach_draft_id=draft.id,
            event_type="sent_manually",
            occurred_at=datetime.now(UTC),
            metadata={"execution": "recorded_after_founder_action"},
        ),
        user.id,
    )
    activation.record_event(
        OutreachEventCreate(
            organization_id=organization.id,
            prospect_experiment_link_id=link.id,
            outreach_draft_id=draft.id,
            event_type="reply_received",
            occurred_at=datetime.now(UTC),
            metadata={"outcome": "positive"},
        ),
        user.id,
    )
    assert link.result_status == "positive"
    sent.event_metadata = {"execution": "changed"}
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()

    analysis = revenue.create_sales_analysis(
        SalesAnalysisCreate(
            organization_id=organization.id,
            prospect_id=prospect.id,
            conversation_reference="manual-conversation:1",
            intent="interested",
            sentiment="positive",
            buying_stage="considering",
            recommended_action="Founder should answer the question directly.",
            suggested_reply="Draft response for founder review only.",
            ai_request_id=analysis_request.id,
            customer_reply="This is useful. What would the next step involve?",
            buying_signal="positive",
            objection_type=None,
        ),
        user.id,
    )
    assert analysis.suggested_reply.startswith("Draft response")
    assert db_session.get(OutreachTrackingEvent, sent.id) is not None


def test_generic_outreach_and_cross_tenant_activation_are_rejected(db_session: Session) -> None:
    entities, _, _, prospect, _ = qualified_activation_foundation(db_session, "activation-boundary")
    other, *_ = discovery_foundation(db_session, "activation-other")
    with pytest.raises(GrowthError):
        scoped_activation(db_session, GrowthProspect, prospect.id, other[0].id)
    generic = OutreachDraftCreate(
        organization_id=entities[0].id,
        prospect_id=prospect.id,
        growth_gift_id=uuid4(),
        channel="email",
        subject="Conversion services",
        body="We help businesses optimize conversion.",
        tone="generic",
        evidence_used=[uuid4()],
        ai_request_id=uuid4(),
        subject_options=["Conversion services"],
        opening_sentence="We help businesses optimize conversion.",
        personalized_context="Generic context.",
        problem_observation="Generic observation.",
        gift_explanation="Generic gift.",
        soft_cta="Book a call.",
    )
    with pytest.raises(GrowthError, match="generic agency or AI language"):
        GrowthRevenueService._validate_outreach_language(generic)
