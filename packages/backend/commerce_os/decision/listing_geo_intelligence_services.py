from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.listing_geo_intelligence_models import (
    FAQRecommendation,
    GEOContentRecommendation,
    ListingIntelligenceEvidence,
    ListingIntelligenceRun,
    ListingStrategyRecommendation,
)
from commerce_os.decision.listing_geo_intelligence_schemas import ListingIntelligenceRunCreate
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now

EntityT = TypeVar("EntityT", bound=Base)
LISTING_GEO_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "customer_segment",
        "primary_problem",
        "positioning",
        "unique_value",
        "benefits",
        "feature_translation",
        "trust_elements",
        "objections",
        "competitive_difference",
        "entity_description",
        "important_attributes",
        "customer_questions",
        "answer_strategy",
        "comparison_topics",
        "expert_topics",
        "citation_targets",
        "missing_information",
        "faqs",
    ],
    "properties": {
        "customer_segment": {"type": "string"},
        "primary_problem": {"type": "string"},
        "positioning": {"type": "string"},
        "unique_value": {"type": "string"},
        "benefits": {"type": "array"},
        "feature_translation": {"type": "array"},
        "trust_elements": {"type": "array"},
        "objections": {"type": "array"},
        "competitive_difference": {"type": "string"},
        "entity_description": {"type": "string"},
        "important_attributes": {"type": "array"},
        "customer_questions": {"type": "array"},
        "answer_strategy": {"type": "string"},
        "comparison_topics": {"type": "array"},
        "expert_topics": {"type": "array"},
        "citation_targets": {"type": "array"},
        "missing_information": {"type": "array"},
        "faqs": {"type": "array"},
    },
}
TEMPLATES = {
    "listing_strategy": "Recommend evidence-grounded listing positioning.",
    "geo_content": "Recommend evidence-grounded AI discovery content structure.",
    "listing_geo_combined": "Compose listing and GEO recommendations from shared evidence.",
}
EVIDENCE_TABLES = {
    "customer_language": "customer_language_insights",
    "pain_cluster": "customer_pain_clusters",
    "customer_need": "customer_needs",
    "marketplace_review": "marketplace_review_evidence",
    "research_analysis": "research_analyses",
}
TRANSITIONS = {
    "draft": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


def scoped_listing_intelligence(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise DecisionScopeError("Listing intelligence record was not found in this organization.")
    return entity


class ListingIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self, payload: ListingIntelligenceRunCreate, actor_id: UUID
    ) -> ListingIntelligenceRun:
        if payload.product_id is None and payload.opportunity_candidate_id is None:
            raise DecisionStateError(
                "Listing intelligence requires a product or opportunity candidate."
            )
        if payload.product_id:
            self._reference("products", payload.product_id, payload.organization_id)
        if payload.opportunity_candidate_id:
            self._reference(
                "opportunity_discovery_candidates",
                payload.opportunity_candidate_id,
                payload.organization_id,
            )
        self._reference("ai_model_capabilities", payload.capability_id, payload.organization_id)
        if payload.prompt_version_id:
            self._reference("prompt_versions", payload.prompt_version_id, payload.organization_id)
        run = ListingIntelligenceRun(
            **payload.model_dump(exclude={"evidence"}),
            status="draft",
            ai_request_id=None,
            created_by=actor_id,
            completed_at=None,
            failure_reason=None,
        )
        self.session.add(run)
        self.session.flush()
        for item in payload.evidence:
            self._reference(
                EVIDENCE_TABLES[item.evidence_type], item.evidence_id, payload.organization_id
            )
            self.session.add(
                ListingIntelligenceEvidence(
                    organization_id=payload.organization_id,
                    listing_run_id=run.id,
                    **item.model_dump(),
                )
            )
        return self._save(run, actor_id, "listing_intelligence.run.created")

    def queue(self, run: ListingIntelligenceRun, actor_id: UUID) -> ListingIntelligenceRun:
        if run.status != "draft" or not self.evidence(run.id, run.organization_id):
            raise DecisionStateError("Only grounded draft listing intelligence may queue.")
        run.status = "queued"
        return self._save(run, actor_id, "listing_intelligence.run.queued")

    def cancel(self, run: ListingIntelligenceRun, actor_id: UUID) -> ListingIntelligenceRun:
        if "cancelled" not in TRANSITIONS[run.status]:
            raise DecisionStateError("Only draft or queued listing intelligence may cancel.")
        run.status, run.completed_at = "cancelled", utc_now()
        return self._save(run, actor_id, "listing_intelligence.run.cancelled")

    def start(
        self, run: ListingIntelligenceRun, request_id: UUID, actor_id: UUID
    ) -> ListingIntelligenceRun:
        if run.status != "queued":
            raise DecisionStateError("Only queued listing intelligence may start.")
        scoped_listing_intelligence(self.session, AIRequest, request_id, run.organization_id)
        run.status, run.ai_request_id = "running", request_id
        return self._save(run, actor_id, "listing_intelligence.run.started", "service")

    def fail(
        self, run: ListingIntelligenceRun, reason: str, actor_id: UUID
    ) -> ListingIntelligenceRun:
        if run.status != "running":
            raise DecisionStateError("Only running listing intelligence may fail.")
        run.status, run.failure_reason, run.completed_at = "failed", reason, utc_now()
        return self._save(run, actor_id, "listing_intelligence.run.failed", "service")

    def complete(
        self, run: ListingIntelligenceRun, content: dict[str, Any], actor_id: UUID
    ) -> ListingStrategyRecommendation:
        if run.status != "running":
            raise DecisionStateError("Only running listing intelligence may complete.")
        evidence = self.evidence(run.id, run.organization_id)
        confidence = round(sum(x.confidence for x in evidence) / len(evidence), 4)
        refs = [
            {
                "type": x.evidence_type,
                "id": str(x.evidence_id),
                "source_reference": x.source_reference,
            }
            for x in evidence
        ]
        listing = ListingStrategyRecommendation(
            organization_id=run.organization_id,
            listing_run_id=run.id,
            customer_segment=str(content["customer_segment"]),
            primary_problem=str(content["primary_problem"]),
            positioning=str(content["positioning"]),
            unique_value=str(content["unique_value"]),
            benefits=list(content["benefits"]),
            feature_translation=list(content["feature_translation"]),
            trust_elements=list(content["trust_elements"]),
            objections=list(content["objections"]),
            competitive_difference=str(content["competitive_difference"]),
            confidence=confidence,
            evidence_refs=refs,
        )
        geo = GEOContentRecommendation(
            organization_id=run.organization_id,
            listing_run_id=run.id,
            entity_description=str(content["entity_description"]),
            important_attributes=list(content["important_attributes"]),
            customer_questions=list(content["customer_questions"]),
            answer_strategy=str(content["answer_strategy"]),
            comparison_topics=list(content["comparison_topics"]),
            expert_topics=list(content["expert_topics"]),
            citation_targets=list(content["citation_targets"]),
            missing_information=list(content["missing_information"]),
            confidence=confidence,
        )
        self.session.add_all([listing, geo])
        self.session.flush()
        for faq in content["faqs"]:
            item = cast(dict[str, Any], faq)
            self.session.add(
                FAQRecommendation(
                    organization_id=run.organization_id,
                    listing_run_id=run.id,
                    question=str(item["question"]),
                    customer_intent=str(item["customer_intent"]),
                    answer_outline=str(item["answer_outline"]),
                    evidence=refs,
                    risk=str(item["risk"]),
                )
            )
        run.status, run.completed_at = "completed", utc_now()
        self.session.flush()
        for entity, action in [
            (listing, "listing_intelligence.strategy.created"),
            (geo, "listing_intelligence.geo.created"),
            (run, "listing_intelligence.run.completed"),
        ]:
            self._audit(entity, actor_id, action, "service")
        self.session.commit()
        self.session.refresh(listing)
        return listing

    def evidence(self, run_id: UUID, organization_id: UUID) -> list[ListingIntelligenceEvidence]:
        scoped_listing_intelligence(self.session, ListingIntelligenceRun, run_id, organization_id)
        return list(
            self.session.scalars(
                select(ListingIntelligenceEvidence).where(
                    ListingIntelligenceEvidence.listing_run_id == run_id
                )
            )
        )

    def _reference(self, table_name: str, entity_id: UUID, organization_id: UUID) -> None:
        table = Base.metadata.tables[table_name]
        if (
            self.session.scalar(
                select(table.c.id).where(
                    table.c.id == entity_id, table.c.organization_id == organization_id
                )
            )
            is None
        ):
            raise DecisionScopeError(
                "Listing intelligence reference was not found in this organization."
            )

    def _audit(self, entity: Any, actor_id: UUID, action: str, actor_type: str) -> None:
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=entity.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )

    def _save(
        self, entity: EntityT, actor_id: UUID, action: str, actor_type: str = "human"
    ) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        self._audit(cast(Any, entity), actor_id, action, actor_type)
        self.session.commit()
        self.session.refresh(entity)
        return entity
