from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIOutputClassification, AIRequest
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import (
    AIModelPolicy,
    GrowthGift,
    GrowthOpportunityAnalysis,
    GrowthOutreachDraft,
    GrowthProspect,
    GrowthProspectEvidence,
    SalesConversationAnalysis,
)
from commerce_os.growth.revenue_schemas import (
    AIModelPolicyCreate,
    GrowthGiftCreate,
    OpportunityAnalysisCreate,
    OutreachDraftCreate,
    ProspectCreate,
    ProspectEvidenceCreate,
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
    "approved": {"ready_for_delivery", "cancelled"},
    "ready_for_delivery": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}
OUTREACH_TRANSITIONS = {
    "draft": {"human_review", "cancelled"},
    "human_review": {"approved", "cancelled"},
    "approved": {"sent", "cancelled"},
    "sent": set(),
    "cancelled": set(),
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
            self._ai_request(payload.ai_request_id, payload.organization_id, {"analysis"})
        values = payload.model_dump()
        values["evidence_reference"] = [str(item) for item in payload.evidence_reference]
        return self._save(
            GrowthOpportunityAnalysis(**values), actor_id, "growthos.opportunity.created"
        )

    def create_gift(self, payload: GrowthGiftCreate, actor_id: UUID) -> GrowthGift:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        opportunity = scoped_revenue(
            self.session, GrowthOpportunityAnalysis, payload.opportunity_id, payload.organization_id
        )
        if opportunity.prospect_id != payload.prospect_id:
            raise GrowthError("Growth Gift opportunity must belong to the selected prospect.")
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
        self, entity: GrowthGift, status: str, actor_id: UUID, approval_id: UUID | None
    ) -> GrowthGift:
        if status not in GIFT_TRANSITIONS[entity.status]:
            raise GrowthError(f"Growth Gift cannot transition from {entity.status} to {status}.")
        if status == "approved":
            self._approval(entity, approval_id, "growth_gift", "approve_growth_gift")
            entity.approval_request_id = approval_id
        if status in {"ready_for_delivery", "delivered"} and entity.approval_request_id is None:
            raise GrowthError("A Growth Gift cannot be delivered without human approval.")
        entity.status = status
        return self._save(entity, actor_id, f"growthos.gift.{status}")

    def create_outreach(self, payload: OutreachDraftCreate, actor_id: UUID) -> GrowthOutreachDraft:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        gift = scoped_revenue(
            self.session, GrowthGift, payload.growth_gift_id, payload.organization_id
        )
        if gift.prospect_id != payload.prospect_id:
            raise GrowthError("Outreach gift must belong to the selected prospect.")
        if gift.status not in {"approved", "ready_for_delivery", "delivered"}:
            raise GrowthError("Outreach requires an approved Growth Gift.")
        self._ai_request(payload.ai_request_id, payload.organization_id, {"draft"})
        for evidence_id in payload.evidence_used:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != payload.prospect_id:
                raise GrowthError("Outreach evidence must belong to the selected prospect.")
        self._validate_outreach_language(payload)
        values = payload.model_dump()
        values["evidence_used"] = [str(item) for item in payload.evidence_used]
        return self._save(
            GrowthOutreachDraft(**values, status="draft", approval_request_id=None),
            actor_id,
            "growthos.outreach.created",
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
        return self._save(
            SalesConversationAnalysis(**payload.model_dump(), status="draft"),
            actor_id,
            "growthos.sales_analysis.created",
        )

    @staticmethod
    def _validate_outreach_language(payload: OutreachDraftCreate) -> None:
        combined = " ".join(
            [
                *payload.subject_options,
                payload.opening_sentence,
                payload.personalized_context,
                payload.problem_observation,
                payload.gift_explanation,
                payload.soft_cta,
                payload.body,
            ]
        ).casefold()
        forbidden = {
            "we help businesses",
            "optimize conversion",
            "full-service agency",
            "as an ai",
            "ai-generated",
        }
        if any(phrase in combined for phrase in forbidden):
            raise GrowthError(
                "Outreach must use specific human research language, "
                "not generic agency or AI language."
            )

    def create_model_policy(self, payload: AIModelPolicyCreate, actor_id: UUID) -> AIModelPolicy:
        self._organization(payload.organization_id)
        return self._save(
            AIModelPolicy(**payload.model_dump()), actor_id, "growthos.ai_model_policy.created"
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
