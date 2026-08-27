from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.adapters import ProviderAdapter
from commerce_os.ai_runtime.execution import AIExecutionService
from commerce_os.ai_runtime.models import AIOutputClassification, AIRequest
from commerce_os.ai_runtime.schemas import AIExecutionSubmit
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_models import (
    IndustryGrowthEvidence,
    IndustryGrowthProfile,
)
from commerce_os.growth.revenue_models import (
    AIModelPolicy,
    BusinessGrowthProfile,
    GrowthDiagnosis,
    GrowthGift,
    GrowthOfferRecommendation,
    GrowthOpportunityAnalysis,
    GrowthOutreachDraft,
    GrowthProspect,
    GrowthProspectEvidence,
    GrowthProspectRanking,
    IndustryDeliveryKnowledge,
    SalesConversationAnalysis,
)
from commerce_os.growth.revenue_schemas import (
    AIModelPolicyCreate,
    BusinessGrowthProfileCreate,
    GrowthDiagnosisCreate,
    GrowthGiftCreate,
    GrowthPackagePreparationCreate,
    GrowthPackagePreparationRead,
    GrowthRevenueV2Dashboard,
    IndustryDeliveryKnowledgeCreate,
    OfferRecommendationCreate,
    OpportunityAnalysisCreate,
    OutreachDraftCreate,
    ProspectCreate,
    ProspectEvidenceCreate,
    ProspectRankingCreate,
    SalesAnalysisCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
PROSPECT_TRANSITIONS = {
    "discovered": {"researching", "disqualified"},
    "researching": {"qualified", "disqualified"},
    "qualified": {"contacted", "disqualified"},
    "contacted": {"replied", "disqualified"},
    "replied": {"customer", "disqualified"},
    "customer": set(),
    "disqualified": set(),
}
GIFT_TRANSITIONS = {
    "draft": {"review", "cancelled"},
    "review": {"approved", "cancelled"},
    "approved": {"ready_for_delivery", "sent", "cancelled"},
    "ready_for_delivery": {"delivered", "cancelled"},
    "delivered": set(),
    "sent": {"customer_response", "cancelled"},
    "customer_response": {"converted", "cancelled"},
    "converted": set(),
    "cancelled": set(),
}
OUTREACH_TRANSITIONS = {
    "draft": {"human_review", "cancelled"},
    "human_review": {"approved", "cancelled"},
    "approved": {"sent", "cancelled"},
    "sent": set(),
    "cancelled": set(),
}

GROWTH_PACKAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "business_situation",
        "pain_points",
        "customer_impact",
        "recommended_improvements",
        "opportunity_type",
        "recommended_offer",
        "risks",
        "missing_information",
        "confidence",
        "gift",
        "email",
    ],
    "properties": {
        "business_situation": {"type": "string"},
        "pain_points": {"type": "array", "items": {"type": "string"}},
        "customer_impact": {"type": "string"},
        "recommended_improvements": {"type": "array", "items": {"type": "string"}},
        "opportunity_type": {
            "type": "string",
            "enum": [
                "website_conversion",
                "seo",
                "google_business",
                "social_media",
                "content",
                "branding",
                "customer_retention",
                "reputation_management",
                "homepage_fix",
                "booking_experience_fix",
                "google_profile_fix",
                "social_content_fix",
                "review_trust_fix",
                "other",
            ],
        },
        "recommended_offer": {"type": "string"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "gift": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "title",
                "description",
                "before_state",
                "after_state",
                "recommended_improvement",
                "expected_value",
                "customer_rationale",
                "implementation_scope",
                "customer_value_explanation",
            ],
            "properties": {
                key: {"type": "string"}
                for key in [
                    "title",
                    "description",
                    "before_state",
                    "after_state",
                    "recommended_improvement",
                    "expected_value",
                    "customer_rationale",
                    "implementation_scope",
                    "customer_value_explanation",
                ]
            },
        },
        "email": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "subject",
                "body",
                "opening_sentence",
                "personalized_context",
                "problem_observation",
                "gift_explanation",
                "soft_cta",
            ],
            "properties": {
                key: {"type": "string"}
                for key in [
                    "subject",
                    "body",
                    "opening_sentence",
                    "personalized_context",
                    "problem_observation",
                    "gift_explanation",
                    "soft_cta",
                ]
            },
        },
    },
}


def scoped_revenue(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError("GrowthOS record was not found in this organization.", "not_found")
    return entity


class GrowthRevenueService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_prospect(self, payload: ProspectCreate, actor_id: UUID) -> GrowthProspect:
        self._organization(payload.organization_id)
        return self._save(
            GrowthProspect(**payload.model_dump(), status="discovered", source_candidate_id=None),
            actor_id,
            "growthos.prospect.created",
        )

    def transition_prospect(
        self, entity: GrowthProspect, status: str, actor_id: UUID
    ) -> GrowthProspect:
        if status not in PROSPECT_TRANSITIONS[entity.status]:
            raise GrowthError(f"Prospect cannot transition from {entity.status} to {status}.")
        if status == "contacted":
            approved = self.session.scalar(
                select(func.count())
                .select_from(GrowthOutreachDraft)
                .where(
                    GrowthOutreachDraft.organization_id == entity.organization_id,
                    GrowthOutreachDraft.prospect_id == entity.id,
                    GrowthOutreachDraft.status == "sent",
                )
            )
            if not approved:
                raise GrowthError(
                    "Contacted status requires a human-approved sent outreach record."
                )
        entity.status = status
        return self._save(entity, actor_id, f"growthos.prospect.{status}")

    def create_evidence(
        self, payload: ProspectEvidenceCreate, actor_id: UUID
    ) -> GrowthProspectEvidence:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        return self._save(
            GrowthProspectEvidence(**payload.model_dump()),
            actor_id,
            "growthos.prospect_evidence.created",
        )

    def create_business_profile(
        self, payload: BusinessGrowthProfileCreate, actor_id: UUID
    ) -> BusinessGrowthProfile:
        prospect = scoped_revenue(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        evidence_ids = [str(item) for item in payload.evidence_references]
        for evidence_id in payload.evidence_references:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != prospect.id:
                raise GrowthError("Business profile evidence must belong to the selected prospect.")
        values = payload.model_dump(exclude={"evidence_references"})
        return self._save(
            BusinessGrowthProfile(
                **values,
                industry=prospect.industry,
                location=prospect.location,
                evidence_references=evidence_ids,
            ),
            actor_id,
            "growthos.business_profile.created",
        )

    def rank_prospect(
        self, payload: ProspectRankingCreate, actor_id: UUID
    ) -> GrowthProspectRanking:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        inputs = payload.model_dump(exclude={"organization_id", "prospect_id"})
        missing = [name for name, value in inputs.items() if value is None]
        score = (
            None
            if missing
            else round(sum(float(value) for value in inputs.values()) / len(inputs), 2)
        )
        explanation = (
            f"Score unavailable; missing: {', '.join(missing)}."
            if missing
            else "Arithmetic mean of supplied pain, impact, accessibility, buying, and fit inputs."
        )
        entity = self.session.scalar(
            select(GrowthProspectRanking).where(
                GrowthProspectRanking.prospect_id == payload.prospect_id
            )
        )
        values = {
            **payload.model_dump(),
            "score": score,
            "missing_inputs": missing,
            "explanation": explanation,
            "formula_version": "growth-revenue-ranking-v1",
        }
        if entity is None:
            entity = GrowthProspectRanking(**values)
        else:
            for name, value in values.items():
                setattr(entity, name, value)
        return self._save(entity, actor_id, "growthos.prospect_ranking.recorded")

    def create_opportunity(
        self, payload: OpportunityAnalysisCreate, actor_id: UUID
    ) -> GrowthOpportunityAnalysis:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        for evidence_id in payload.evidence_reference:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != payload.prospect_id:
                raise GrowthError("Opportunity evidence must belong to the selected prospect.")
        if payload.ai_request_id is not None:
            self._ai_request(payload.ai_request_id, payload.organization_id, {"analysis", "draft"})
        values = payload.model_dump()
        values["evidence_reference"] = [str(item) for item in payload.evidence_reference]
        return self._save(
            GrowthOpportunityAnalysis(**values), actor_id, "growthos.opportunity.created"
        )

    def create_diagnosis(self, payload: GrowthDiagnosisCreate, actor_id: UUID) -> GrowthDiagnosis:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if payload.industry_profile_id is not None:
            profile = self.session.get(IndustryGrowthProfile, payload.industry_profile_id)
            if profile is None or profile.organization_id != payload.organization_id:
                raise GrowthError("Industry profile was not found in this organization.")
        evidence_ids = [str(item) for item in payload.evidence_references]
        for evidence_id in payload.evidence_references:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != payload.prospect_id:
                raise GrowthError("Diagnosis evidence must belong to the selected prospect.")
        if payload.ai_request_id is not None:
            self._ai_request(payload.ai_request_id, payload.organization_id, {"analysis", "draft"})
        self._reject_unsupported_claims(
            " ".join(
                [
                    payload.business_situation,
                    *payload.growth_problems,
                    payload.customer_impact,
                    *payload.recommended_improvements,
                ]
            )
        )
        values = payload.model_dump(exclude={"evidence_references"})
        return self._save(
            GrowthDiagnosis(**values, evidence_references=evidence_ids, status="draft"),
            actor_id,
            "growthos.diagnosis.created",
        )

    def recommend_offer(
        self, payload: OfferRecommendationCreate, actor_id: UUID
    ) -> GrowthOfferRecommendation:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        diagnosis = scoped_revenue(
            self.session, GrowthDiagnosis, payload.diagnosis_id, payload.organization_id
        )
        if diagnosis.prospect_id != payload.prospect_id:
            raise GrowthError("Offer diagnosis must belong to the selected prospect.")
        if payload.location_count > 1:
            offer_type = "expansion_package"
            rationale = (
                "Multiple locations were explicitly supplied; "
                "expansion coordination is the primary fit."
            )
        elif payload.high_review_weak_visibility:
            offer_type = "visibility_package"
            rationale = (
                "Strong reviews and weak visibility were explicitly supplied; "
                "visibility is the primary gap."
            )
        elif payload.business_stage == "new":
            offer_type = "launch_growth_package"
            rationale = (
                "The business was explicitly identified as new; "
                "launch foundations are the primary fit."
            )
        else:
            offer_type = "growth_optimization_package"
            rationale = (
                "The existing single-location business is best served by focused optimization."
            )
        return self._save(
            GrowthOfferRecommendation(
                organization_id=payload.organization_id,
                prospect_id=payload.prospect_id,
                diagnosis_id=payload.diagnosis_id,
                offer_type=offer_type,
                rationale=rationale,
                customer_fit=payload.customer_fit,
                scope_summary=payload.scope_summary,
                confidence=payload.confidence,
                risks=payload.risks,
                status="draft",
                formula_version="growth-offer-rules-v1",
            ),
            actor_id,
            "growthos.offer_recommendation.created",
        )

    def create_gift(self, payload: GrowthGiftCreate, actor_id: UUID) -> GrowthGift:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        opportunity = scoped_revenue(
            self.session, GrowthOpportunityAnalysis, payload.opportunity_id, payload.organization_id
        )
        if opportunity.prospect_id != payload.prospect_id:
            raise GrowthError("Growth Gift opportunity must belong to the selected prospect.")
        if payload.growth_diagnosis_id is not None:
            diagnosis = scoped_revenue(
                self.session, GrowthDiagnosis, payload.growth_diagnosis_id, payload.organization_id
            )
            if diagnosis.prospect_id != payload.prospect_id:
                raise GrowthError("Growth Gift diagnosis must belong to the selected prospect.")
        evidence_ids = [str(item) for item in payload.evidence_reference]
        if not set(evidence_ids).issubset(set(opportunity.evidence_reference)):
            raise GrowthError("Growth Gift evidence must be cited by its opportunity analysis.")
        for evidence_id in payload.evidence_reference:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != payload.prospect_id:
                raise GrowthError("Growth Gift evidence must belong to the selected prospect.")
        values = payload.model_dump()
        values["evidence_reference"] = evidence_ids
        return self._save(
            GrowthGift(**values, status="draft", approval_request_id=None),
            actor_id,
            "growthos.gift.created",
        )

    def transition_gift(
        self,
        entity: GrowthGift,
        status: str,
        actor_id: UUID,
        approval_id: UUID | None,
        customer_response: str | None = None,
    ) -> GrowthGift:
        if status not in GIFT_TRANSITIONS[entity.status]:
            raise GrowthError(f"Growth Gift cannot transition from {entity.status} to {status}.")
        if status == "approved":
            self._approval(entity, approval_id, "growth_gift", "approve_growth_gift")
            entity.approval_request_id = approval_id
        if status in {"ready_for_delivery", "delivered"} and entity.approval_request_id is None:
            raise GrowthError("A Growth Gift cannot be delivered without human approval.")
        if status == "sent" and entity.approval_request_id is None:
            raise GrowthError("A Growth Gift cannot be recorded as sent without human approval.")
        if status == "customer_response":
            if not customer_response:
                raise GrowthError("Customer response state requires the observed response.")
            entity.customer_response = customer_response
        entity.status = status
        return self._save(entity, actor_id, f"growthos.gift.{status}")

    def create_outreach(self, payload: OutreachDraftCreate, actor_id: UUID) -> GrowthOutreachDraft:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        gift = scoped_revenue(
            self.session, GrowthGift, payload.growth_gift_id, payload.organization_id
        )
        if gift.prospect_id != payload.prospect_id:
            raise GrowthError("Outreach gift must belong to the selected prospect.")
        if gift.status == "cancelled":
            raise GrowthError("Outreach cannot be drafted from a cancelled Growth Gift.")
        message_versions = payload.message_versions or {
            "founder_friendly": payload.body,
            "consultant": payload.body,
            "gift_first": payload.body,
        }
        if set(message_versions) != {"founder_friendly", "consultant", "gift_first"}:
            raise GrowthError(
                "Outreach requires founder-friendly, consultant, and gift-first versions."
            )
        if payload.growth_diagnosis_id is not None:
            diagnosis = scoped_revenue(
                self.session, GrowthDiagnosis, payload.growth_diagnosis_id, payload.organization_id
            )
            if diagnosis.prospect_id != payload.prospect_id:
                raise GrowthError("Outreach diagnosis must belong to the selected prospect.")
        if payload.industry_profile_id is not None:
            profile = self.session.get(IndustryGrowthProfile, payload.industry_profile_id)
            if profile is None or profile.organization_id != payload.organization_id:
                raise GrowthError("Industry profile was not found in this organization.")
            if not payload.industry_context:
                raise GrowthError("Industry-aware outreach requires explicit industry context.")
        self._ai_request(payload.ai_request_id, payload.organization_id, {"draft"})
        for evidence_id in payload.evidence_used:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != payload.prospect_id:
                raise GrowthError("Outreach evidence must belong to the selected prospect.")
        self._validate_outreach_language(payload, message_versions)
        values = payload.model_dump()
        values["evidence_used"] = [str(item) for item in payload.evidence_used]
        values["message_versions"] = message_versions
        return self._save(
            GrowthOutreachDraft(**values, status="draft", approval_request_id=None),
            actor_id,
            "growthos.outreach.created",
        )

    def prepare_growth_package(
        self,
        payload: GrowthPackagePreparationCreate,
        actor_id: UUID,
        adapters: dict[str, ProviderAdapter] | None = None,
    ) -> GrowthPackagePreparationRead:
        prospect = scoped_revenue(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        evidence = list(
            self.session.scalars(
                select(GrowthProspectEvidence).where(
                    GrowthProspectEvidence.organization_id == payload.organization_id,
                    GrowthProspectEvidence.prospect_id == prospect.id,
                )
            )
        )
        if not evidence:
            raise GrowthError("Growth package preparation requires traceable prospect evidence.")
        execution = AIExecutionService(self.session, adapters)
        request = execution.submit(
            AIExecutionSubmit(
                organization_id=payload.organization_id,
                purpose="Prepare evidence-backed Growth Gift and outreach drafts",
                context_type="growth_prospect",
                context_reference=str(prospect.id),
                capability_id=payload.capability_id,
                task_type="growth_package_preparation",
                system_instructions=(
                    "Use only the supplied public evidence. Produce a concise advisory growth "
                    "diagnosis, a useful before/after preview concept, and a natural founder email "
                    "draft for human review. Cite no unsupported claims, promise no revenue, and "
                    "keep unknown facts in missing_information. The output is draft material only; "
                    "it cannot approve, send, publish, spend, or make a commitment."
                ),
                input_content=str(
                    {
                        "business": prospect.business_name,
                        "industry": prospect.industry,
                        "location": prospect.location,
                        "website": prospect.website,
                        "evidence": [
                            {
                                "id": str(item.id),
                                "observation": item.observation,
                                "source_url": item.source_url,
                                "confidence": item.confidence,
                            }
                            for item in evidence
                        ],
                        "founder_feedback": payload.founder_feedback,
                    }
                ),
                output_classification="draft",
                expected_output_schema=GROWTH_PACKAGE_OUTPUT_SCHEMA,
                runtime_configuration={"max_output_tokens": 3500},
                provenance_context={"source_domain": "growth", "prospect_id": str(prospect.id)},
            ),
            actor_id,
        )
        request = execution.execute(request)
        if str(request.status) != "succeeded" or request.response_content is None:
            raise GrowthError(request.failure_reason or "Growth package preparation failed.")
        content = request.response_content
        confidence = float(content["confidence"])
        evidence_ids = [item.id for item in evidence]
        opportunity = self.create_opportunity(
            OpportunityAnalysisCreate(
                organization_id=payload.organization_id,
                prospect_id=prospect.id,
                opportunity_type=str(content["opportunity_type"]),
                problem_statement="; ".join(str(x) for x in content["pain_points"]),
                evidence_reference=evidence_ids,
                customer_impact=str(content["customer_impact"]),
                purchase_probability=None,
                confidence=confidence,
                recommended_offer=str(content["recommended_offer"]),
                risks=[str(x) for x in content["risks"]],
                missing_information=[str(x) for x in content["missing_information"]],
                ai_request_id=request.id,
            ),
            actor_id,
        )
        diagnosis = self.create_diagnosis(
            GrowthDiagnosisCreate(
                organization_id=payload.organization_id,
                prospect_id=prospect.id,
                business_situation=str(content["business_situation"]),
                growth_problems=[str(x) for x in content["pain_points"]],
                evidence_references=evidence_ids,
                customer_impact=str(content["customer_impact"]),
                recommended_improvements=[str(x) for x in content["recommended_improvements"]],
                confidence=confidence,
                risks=[str(x) for x in content["risks"]],
                ai_request_id=request.id,
            ),
            actor_id,
        )
        gift_data = cast(dict[str, Any], content["gift"])
        gift = self.create_gift(
            GrowthGiftCreate(
                organization_id=payload.organization_id,
                prospect_id=prospect.id,
                opportunity_id=opportunity.id,
                title=str(gift_data["title"]),
                description=str(gift_data["description"]),
                before_state=str(gift_data["before_state"]),
                after_state=str(gift_data["after_state"]),
                evidence_reference=evidence_ids,
                observed_issue="; ".join(str(x) for x in content["pain_points"]),
                recommended_improvement=str(gift_data["recommended_improvement"]),
                expected_value=str(gift_data["expected_value"]),
                preview_type="other",
                preview_status="draft",
                gift_type="other",
                customer_rationale=str(gift_data["customer_rationale"]),
                growth_diagnosis_id=diagnosis.id,
                personalized_diagnosis=str(content["business_situation"]),
                implementation_scope=str(gift_data["implementation_scope"]),
                customer_value_explanation=str(gift_data["customer_value_explanation"]),
            ),
            actor_id,
        )
        email = cast(dict[str, Any], content["email"])
        body = str(email["body"])
        outreach = self.create_outreach(
            OutreachDraftCreate(
                organization_id=payload.organization_id,
                prospect_id=prospect.id,
                growth_gift_id=gift.id,
                channel="email",
                subject=str(email["subject"]),
                body=body,
                tone="founder_evidence_first",
                evidence_used=evidence_ids,
                ai_request_id=request.id,
                industry_context=prospect.industry,
                subject_options=[str(email["subject"])],
                opening_sentence=str(email["opening_sentence"]),
                personalized_context=str(email["personalized_context"]),
                problem_observation=str(email["problem_observation"]),
                gift_explanation=str(email["gift_explanation"]),
                soft_cta=str(email["soft_cta"]),
                growth_diagnosis_id=diagnosis.id,
                message_versions={"founder_friendly": body, "consultant": body, "gift_first": body},
            ),
            actor_id,
        )
        return GrowthPackagePreparationRead(
            ai_request_id=request.id,
            opportunity_id=opportunity.id,
            diagnosis_id=diagnosis.id,
            growth_gift_id=gift.id,
            outreach_draft_id=outreach.id,
            revision_note="New version created from current evidence and founder feedback.",
        )

    def transition_outreach(
        self, entity: GrowthOutreachDraft, status: str, actor_id: UUID, approval_id: UUID | None
    ) -> GrowthOutreachDraft:
        if status not in OUTREACH_TRANSITIONS[entity.status]:
            raise GrowthError(f"Outreach cannot transition from {entity.status} to {status}.")
        if status == "approved":
            self._approval(entity, approval_id, "growth_outreach_draft", "approve_outreach")
            entity.approval_request_id = approval_id
        if status == "sent" and entity.approval_request_id is None:
            raise GrowthError("External communication requires human approval.")
        if status == "sent":
            gift = scoped_revenue(
                self.session, GrowthGift, entity.growth_gift_id, entity.organization_id
            )
            if gift.status not in {"approved", "ready_for_delivery", "delivered", "sent"}:
                raise GrowthError("External communication requires an approved Growth Gift.")
        entity.status = status
        return self._save(entity, actor_id, f"growthos.outreach.{status}")

    def create_sales_analysis(
        self, payload: SalesAnalysisCreate, actor_id: UUID
    ) -> SalesConversationAnalysis:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        self._ai_request(
            payload.ai_request_id,
            payload.organization_id,
            {"analysis", "recommendation", "draft", "classification"},
        )
        if payload.industry_profile_id is not None:
            profile = self.session.get(IndustryGrowthProfile, payload.industry_profile_id)
            if profile is None or profile.organization_id != payload.organization_id:
                raise GrowthError("Industry profile was not found in this organization.")
            if not payload.industry_context:
                raise GrowthError(
                    "Industry-aware sales analysis requires explicit industry context."
                )
        return self._save(
            SalesConversationAnalysis(
                **payload.model_dump(exclude={"reply_classification"}),
                reply_classification=payload.reply_classification
                or {
                    "not_interested": "not_now",
                    "wrong_person": "referral",
                    "needs_time": "not_now",
                }.get(payload.intent, payload.intent),
                status="draft",
            ),
            actor_id,
            "growthos.sales_analysis.created",
        )

    def create_delivery_knowledge(
        self, payload: IndustryDeliveryKnowledgeCreate, actor_id: UUID
    ) -> IndustryDeliveryKnowledge:
        profile = self.session.get(IndustryGrowthProfile, payload.industry_profile_id)
        if profile is None or profile.organization_id != payload.organization_id:
            raise GrowthError("Industry profile was not found in this organization.")
        evidence_ids = [str(item) for item in payload.evidence_references]
        for evidence_id in payload.evidence_references:
            evidence = self.session.get(IndustryGrowthEvidence, evidence_id)
            if (
                evidence is None
                or evidence.organization_id != payload.organization_id
                or evidence.industry_profile_id != payload.industry_profile_id
            ):
                raise GrowthError(
                    "Delivery knowledge evidence must belong to the industry profile."
                )
        values = payload.model_dump(exclude={"evidence_references"})
        return self._save(
            IndustryDeliveryKnowledge(**values, evidence_references=evidence_ids, status="active"),
            actor_id,
            "growthos.industry_delivery_knowledge.created",
        )

    @staticmethod
    def _reject_unsupported_claims(content: str) -> None:
        prohibited = {"guaranteed revenue", "guaranteed roi", "10x revenue", "guaranteed results"}
        if any(claim in content.casefold() for claim in prohibited):
            raise GrowthError("Diagnosis cannot contain unsupported revenue or outcome promises.")

    @staticmethod
    def _validate_outreach_language(
        payload: OutreachDraftCreate, message_versions: Mapping[Any, str] | None = None
    ) -> None:
        versions = message_versions or payload.message_versions
        combined = " ".join(
            [
                *payload.subject_options,
                payload.opening_sentence,
                payload.personalized_context,
                payload.problem_observation,
                payload.gift_explanation,
                payload.soft_cta,
                payload.body,
                *versions.values(),
            ]
        ).casefold()
        forbidden = {
            "we help businesses",
            "optimize conversion",
            "full-service agency",
            "as an ai",
            "ai-generated",
            "guaranteed roi",
            "guaranteed results",
            "10x your revenue",
        }
        if any(phrase in combined for phrase in forbidden):
            raise GrowthError(
                "Outreach must use specific human research language, "
                "not generic agency or AI language."
            )

    def create_model_policy(self, payload: AIModelPolicyCreate, actor_id: UUID) -> AIModelPolicy:
        self._organization(payload.organization_id)
        if payload.cost_policy == "capped" and payload.cost_limit is None:
            raise GrowthError("Capped model routing requires an explicit cost limit.")
        return self._save(
            AIModelPolicy(**payload.model_dump()), actor_id, "growthos.ai_model_policy.created"
        )

    def v2_dashboard(self, organization_id: UUID) -> GrowthRevenueV2Dashboard:
        self._organization(organization_id)

        def count(table_name: str, *criteria: ColumnElement[bool]) -> int:
            table = Base.metadata.tables[table_name]
            return int(
                self.session.execute(
                    select(func.count())
                    .select_from(table)
                    .where(table.c.organization_id == organization_id, *criteria)
                ).scalar_one()
                or 0
            )

        prospects = Base.metadata.tables["growth_prospects"]
        demand = Base.metadata.tables["demand_signals"]
        pipeline = {
            status: count("growth_prospects", prospects.c.status == status)
            for status in [
                "discovered",
                "researching",
                "qualified",
                "contacted",
                "replied",
                "customer",
            ]
        }
        return GrowthRevenueV2Dashboard(
            organization_id=organization_id,
            business_profiles=count("business_growth_profiles"),
            ranked_prospects=count("growth_prospect_rankings"),
            pipeline=pipeline,
            growth_demand_signals=count(
                "demand_signals", demand.c.source_type == "growthos_conversation"
            ),
            commerce_independent_demand_signals=count(
                "demand_signals", demand.c.source_type != "growthos_conversation"
            ),
        )

    def _ai_request(self, request_id: UUID, organization_id: UUID, allowed: set[str]) -> AIRequest:
        request = self.session.get(AIRequest, request_id)
        if request is None or request.organization_id != organization_id:
            raise GrowthError("AI request was not found in this organization.", "not_found")
        classification = (
            request.output_classification.value
            if isinstance(request.output_classification, AIOutputClassification)
            else request.output_classification
        )
        if request.status not in {"completed", "succeeded"} or classification not in allowed:
            raise GrowthError("GrowthOS output requires a completed governed AI request.")
        if not request.task_type or not request.selected_model_identity:
            raise GrowthError("AI request is missing task type or model provenance.")
        return request

    def _approval(
        self,
        entity: GrowthGift | GrowthOutreachDraft,
        approval_id: UUID | None,
        object_type: str,
        action: str,
    ) -> None:
        if approval_id is None:
            raise GrowthError("This transition requires human Governance approval.")
        table = Base.metadata.tables["approval_requests"]
        row = (
            self.session.execute(
                table.select().where(
                    table.c.id == approval_id,
                    table.c.organization_id == entity.organization_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            row is None
            or row["status"] != "approved"
            or row["object_type"] != object_type
            or row["object_id"] != entity.id
            or row["requested_action"] != action
        ):
            raise GrowthError("Governance approval does not authorize this transition.")

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if self.session.scalar(select(table.c.id).where(table.c.id == organization_id)) is None:
            raise GrowthError("Organization was not found.", "not_found")

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
