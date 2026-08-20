from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.decision.creative_intelligence_models import (
    CreativeAngle,
    CreativeBriefRecommendation,
    CreativeIntelligenceEvidence,
    CreativeIntelligenceRun,
    CreativeStrategyRecommendation,
)
from commerce_os.decision.creative_intelligence_schemas import CreativeIntelligenceRunCreate
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now

EntityT = TypeVar("EntityT", bound=Base)
CREATIVE_INTELLIGENCE_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "customer",
        "problem",
        "hook",
        "message",
        "creative_angle",
        "visual_direction",
        "proof_points",
        "risks",
    ],
    "properties": {
        "customer": {"type": "string"},
        "problem": {"type": "string"},
        "hook": {"type": "string"},
        "message": {"type": "string"},
        "creative_angle": {"type": "string"},
        "visual_direction": {"type": "string"},
        "proof_points": {"type": "array"},
        "risks": {"type": "array"},
        "objections": {"type": "array"},
        "channel": {"type": "string"},
        "cta": {"type": "string"},
        "estimated_impact": {"type": "string"},
    },
}
TEMPLATES = {
    "pain_message": "Ground messaging in an evidenced customer pain.",
    "transformation_message": "Draft an evidenced before-to-after transformation.",
    "trust_message": "Draft trust messaging using supplied proof only.",
    "education_message": "Draft educational messaging from supplied customer needs.",
}
EVIDENCE_TABLES = {
    "customer_language": "customer_language_insights",
    "pain_cluster": "customer_pain_clusters",
    "customer_need": "customer_needs",
}
TRANSITIONS = {
    "draft": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}
CHANNELS = {"TikTok", "Instagram", "Facebook", "Pinterest", "YouTube Shorts"}


def scoped_creative_intelligence(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise DecisionScopeError("Creative intelligence record was not found in this organization.")
    return entity


class CreativeIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self, payload: CreativeIntelligenceRunCreate, actor_id: UUID
    ) -> CreativeIntelligenceRun:
        if payload.opportunity_candidate_id is None and payload.product_id is None:
            raise DecisionStateError(
                "Creative intelligence requires an opportunity candidate or product."
            )
        if payload.opportunity_candidate_id:
            self._reference(
                "opportunity_discovery_candidates",
                payload.opportunity_candidate_id,
                payload.organization_id,
            )
        if payload.product_id:
            self._reference("products", payload.product_id, payload.organization_id)
        self._reference("ai_model_capabilities", payload.capability_id, payload.organization_id)
        if payload.prompt_version_id:
            self._reference("prompt_versions", payload.prompt_version_id, payload.organization_id)
        run = CreativeIntelligenceRun(
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
                CreativeIntelligenceEvidence(
                    organization_id=payload.organization_id,
                    creative_run_id=run.id,
                    **item.model_dump(),
                )
            )
        return self._save(run, actor_id, "creative_intelligence.run.created")

    def queue(self, run: CreativeIntelligenceRun, actor_id: UUID) -> CreativeIntelligenceRun:
        if run.status != "draft" or not self.evidence(run.id, run.organization_id):
            raise DecisionStateError("Only grounded draft creative intelligence may be queued.")
        run.status = "queued"
        return self._save(run, actor_id, "creative_intelligence.run.queued")

    def cancel(self, run: CreativeIntelligenceRun, actor_id: UUID) -> CreativeIntelligenceRun:
        if "cancelled" not in TRANSITIONS[run.status]:
            raise DecisionStateError("Only draft or queued creative intelligence may be cancelled.")
        run.status, run.completed_at = "cancelled", utc_now()
        return self._save(run, actor_id, "creative_intelligence.run.cancelled")

    def start(
        self, run: CreativeIntelligenceRun, request_id: UUID, actor_id: UUID
    ) -> CreativeIntelligenceRun:
        if run.status != "queued":
            raise DecisionStateError("Only queued creative intelligence may start.")
        scoped_creative_intelligence(self.session, AIRequest, request_id, run.organization_id)
        run.status, run.ai_request_id = "running", request_id
        return self._save(run, actor_id, "creative_intelligence.run.started", "service")

    def fail(
        self, run: CreativeIntelligenceRun, reason: str, actor_id: UUID
    ) -> CreativeIntelligenceRun:
        if run.status != "running":
            raise DecisionStateError("Only running creative intelligence may fail.")
        run.status, run.failure_reason, run.completed_at = "failed", reason, utc_now()
        return self._save(run, actor_id, "creative_intelligence.run.failed", "service")

    def complete(
        self, run: CreativeIntelligenceRun, content: dict[str, Any], actor_id: UUID
    ) -> CreativeStrategyRecommendation:
        if run.status != "running":
            raise DecisionStateError("Only running creative intelligence may complete.")
        evidence = self.evidence(run.id, run.organization_id)
        confidence = round(sum(item.confidence for item in evidence) / len(evidence), 4)
        refs = [
            {
                "type": item.evidence_type,
                "id": str(item.evidence_id),
                "source_reference": item.source_reference,
            }
            for item in evidence
        ]
        channel = str(content.get("channel", "TikTok"))
        if channel not in CHANNELS:
            raise DecisionStateError("Creative channel is not supported.")
        proof = list(content["proof_points"])
        risks = list(content["risks"])
        objections = list(content.get("objections", []))
        recommendation = CreativeStrategyRecommendation(
            organization_id=run.organization_id,
            creative_run_id=run.id,
            target_customer=str(content["customer"]),
            customer_problem=str(content["problem"]),
            core_message=str(content["message"]),
            value_proposition=str(content["message"]),
            emotional_angle=str(content["creative_angle"]),
            rational_angle=str(content["message"]),
            trust_elements=proof,
            objections=objections,
            channel_recommendations=[channel],
            confidence_score=confidence,
            risks=risks,
            estimated_impact=content.get("estimated_impact"),
            output_type="recommendation",
        )
        angle = CreativeAngle(
            organization_id=run.organization_id,
            creative_run_id=run.id,
            angle_type=run.template_type,
            content=str(content["creative_angle"]),
            evidence_references=refs,
            confidence=confidence,
            source="governed_ai_recommendation",
        )
        visual = str(content["visual_direction"])
        cta = str(content.get("cta", content["message"]))
        brief = CreativeBriefRecommendation(
            organization_id=run.organization_id,
            creative_run_id=run.id,
            hook=str(content["hook"]),
            problem=str(content["problem"]),
            solution=str(content["message"]),
            proof=proof,
            cta=cta,
            visual_direction=visual,
            video_concept=visual,
            image_concept=visual,
            ugc_concept=visual,
            audience=str(content["customer"]),
            channel=channel,
            evidence_references=refs,
        )
        self.session.add_all([recommendation, angle, brief])
        self.session.flush()
        run.status, run.completed_at = "completed", utc_now()
        for entity, action in [
            (recommendation, "creative_intelligence.strategy.created"),
            (brief, "creative_intelligence.brief.created"),
            (run, "creative_intelligence.run.completed"),
        ]:
            self._audit(entity, actor_id, action, "service")
        self.session.commit()
        self.session.refresh(recommendation)
        return recommendation

    def evidence(self, run_id: UUID, organization_id: UUID) -> list[CreativeIntelligenceEvidence]:
        scoped_creative_intelligence(self.session, CreativeIntelligenceRun, run_id, organization_id)
        return list(
            self.session.scalars(
                select(CreativeIntelligenceEvidence).where(
                    CreativeIntelligenceEvidence.creative_run_id == run_id
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
                "Creative intelligence reference was not found in this organization."
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
