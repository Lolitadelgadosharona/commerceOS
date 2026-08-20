from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.intelligence.discovery_models import (
    OpportunityCandidate,
    OpportunityDiscoveryEvidence,
    OpportunityDiscoveryRun,
)
from commerce_os.intelligence.discovery_schemas import (
    DiscoveryTemplateRead,
    OpportunityDiscoveryRunCreate,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.research_models import ResearchRun
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now

EntityT = TypeVar("EntityT", bound=Base)
DISCOVERY_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "title",
        "problem",
        "customer_segment",
        "evidence_summary",
        "solution_direction",
        "customer_language",
        "risks",
        "confidence",
        "open_questions",
        "missing_evidence",
    ],
    "properties": {
        "title": {"type": "string"},
        "problem": {"type": "string"},
        "customer_segment": {"type": "string"},
        "evidence_summary": {"type": "string"},
        "solution_direction": {"type": "string"},
        "customer_language": {"type": "array"},
        "risks": {"type": "array"},
        "confidence": {"type": "number"},
        "open_questions": {"type": "array"},
        "missing_evidence": {"type": "array"},
    },
}
DISCOVERY_TEMPLATES = {
    "reddit_pain_discovery": (
        "Identify repeated customer problems from Reddit evidence.",
        ["pain_candidate", "pain_cluster"],
    ),
    "marketplace_review_discovery": (
        "Identify product improvement opportunities from marketplace reviews.",
        ["marketplace_review"],
    ),
    "trend_opportunity_discovery": (
        "Identify emerging demand from market signals.",
        ["market_signal"],
    ),
    "cross_source_opportunity_discovery": (
        "Combine multiple existing evidence and research sources.",
        [
            "market_signal",
            "pain_candidate",
            "pain_cluster",
            "marketplace_review",
            "research_analysis",
            "customer_need",
        ],
    ),
}
EVIDENCE_TABLES = {
    "market_signal": "market_signals",
    "pain_candidate": "customer_pain_candidates",
    "pain_cluster": "customer_pain_clusters",
    "marketplace_review": "marketplace_review_evidence",
    "research_analysis": "research_analyses",
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


def scoped_discovery(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Opportunity discovery record was not found in this organization."
        )
    return entity


class OpportunityDiscoveryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self, payload: OpportunityDiscoveryRunCreate, actor_id: UUID
    ) -> OpportunityDiscoveryRun:
        if payload.project_id:
            self._reference("projects", payload.project_id, payload.organization_id)
        if payload.research_run_id:
            research = scoped_discovery(
                self.session, ResearchRun, payload.research_run_id, payload.organization_id
            )
            if research.status != "completed":
                raise IntelligenceValidationError("Linked research run must be completed.")
        self._reference("ai_model_capabilities", payload.capability_id, payload.organization_id)
        if payload.prompt_version_id:
            self._reference("prompt_versions", payload.prompt_version_id, payload.organization_id)
        run = OpportunityDiscoveryRun(
            **payload.model_dump(exclude={"evidence"}),
            status="draft",
            created_by=actor_id,
            ai_request_id=None,
            started_at=None,
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
                OpportunityDiscoveryEvidence(
                    organization_id=payload.organization_id,
                    discovery_run_id=run.id,
                    **item.model_dump(),
                )
            )
        return self._save(run, actor_id, "opportunity_discovery.run.created")

    def queue(self, run: OpportunityDiscoveryRun, actor_id: UUID) -> OpportunityDiscoveryRun:
        if run.status != "draft":
            raise IntelligenceValidationError("Only draft discovery runs may be queued.")
        types = {row.evidence_type for row in self.evidence(run.id, run.organization_id)}
        required = set(DISCOVERY_TEMPLATES[run.discovery_type][1])
        if not types.intersection(required):
            raise IntelligenceValidationError("Discovery evidence does not satisfy its template.")
        run.status = "queued"
        return self._save(run, actor_id, "opportunity_discovery.run.queued")

    def cancel(self, run: OpportunityDiscoveryRun, actor_id: UUID) -> OpportunityDiscoveryRun:
        if "cancelled" not in TRANSITIONS[run.status]:
            raise IntelligenceValidationError(
                "Only draft or queued discovery runs may be cancelled."
            )
        run.status, run.completed_at = "cancelled", utc_now()
        return self._save(run, actor_id, "opportunity_discovery.run.cancelled")

    def start(
        self, run: OpportunityDiscoveryRun, request_id: UUID, actor_id: UUID
    ) -> OpportunityDiscoveryRun:
        if run.status != "queued":
            raise IntelligenceValidationError("Only queued discovery runs may start.")
        scoped_discovery(self.session, AIRequest, request_id, run.organization_id)
        run.status, run.ai_request_id, run.started_at = "running", request_id, utc_now()
        return self._save(run, actor_id, "opportunity_discovery.run.started", "service")

    def fail(
        self, run: OpportunityDiscoveryRun, reason: str, actor_id: UUID
    ) -> OpportunityDiscoveryRun:
        if run.status != "running":
            raise IntelligenceValidationError("Only running discovery may fail.")
        run.status, run.failure_reason, run.completed_at = "failed", reason, utc_now()
        return self._save(run, actor_id, "opportunity_discovery.run.failed", "service")

    def complete(
        self, run: OpportunityDiscoveryRun, content: dict[str, Any], actor_id: UUID
    ) -> OpportunityCandidate:
        if run.status != "running":
            raise IntelligenceValidationError("Only running discovery may complete.")
        confidence = float(content["confidence"])  # schema validation precedes this boundary
        if not 0 <= confidence <= 1:
            raise IntelligenceValidationError("Discovery confidence must be between zero and one.")
        references = [
            {
                "type": row.evidence_type,
                "id": str(row.evidence_id),
                "source_reference": row.source_reference,
            }
            for row in self.evidence(run.id, run.organization_id)
        ]
        candidate = OpportunityCandidate(
            organization_id=run.organization_id,
            discovery_run_id=run.id,
            title=str(content["title"]),
            problem_statement=str(content["problem"]),
            customer_segment=str(content["customer_segment"]),
            evidence_summary=str(content["evidence_summary"]),
            evidence_references=references,
            solution_direction=str(content["solution_direction"]),
            customer_language=list(content["customer_language"]),
            confidence_score=confidence,
            risk_summary=list(content["risks"]),
            open_questions=list(content["open_questions"]),
            missing_evidence=list(content["missing_evidence"]),
            advisory_score=round(confidence * 100, 2),
            status="draft",
            methodology_version=run.methodology_version,
            decision_queue_item_id=None,
        )
        self.session.add(candidate)
        self.session.flush()
        run.status, run.completed_at = "completed", utc_now()
        record_audit_event(
            self.session,
            organization_id=run.organization_id,
            actor_type="service",
            actor_id=actor_id,
            action="opportunity_discovery.candidate.created",
            entity_type=candidate.__tablename__,
            entity_id=candidate.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        record_audit_event(
            self.session,
            organization_id=run.organization_id,
            actor_type="service",
            actor_id=actor_id,
            action="opportunity_discovery.run.completed",
            entity_type=run.__tablename__,
            entity_id=run.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(candidate)
        return candidate

    def mark_review(
        self, candidate: OpportunityCandidate, queue_id: UUID, actor_id: UUID
    ) -> OpportunityCandidate:
        if candidate.status != "draft" or candidate.decision_queue_item_id is not None:
            raise IntelligenceValidationError("Only an unqueued draft candidate may enter review.")
        candidate.status, candidate.decision_queue_item_id = "review", queue_id
        return self._save(candidate, actor_id, "opportunity_discovery.candidate.review_queued")

    def evidence(self, run_id: UUID, organization_id: UUID) -> list[OpportunityDiscoveryEvidence]:
        scoped_discovery(self.session, OpportunityDiscoveryRun, run_id, organization_id)
        return list(
            self.session.scalars(
                select(OpportunityDiscoveryEvidence).where(
                    OpportunityDiscoveryEvidence.discovery_run_id == run_id
                )
            )
        )

    @staticmethod
    def templates() -> list[DiscoveryTemplateRead]:
        return [
            DiscoveryTemplateRead(
                discovery_type=cast(Any, key),
                purpose=value[0],
                evidence_requirements=cast(Any, value[1]),
                expected_output_schema=DISCOVERY_OUTPUT_SCHEMA,
            )
            for key, value in DISCOVERY_TEMPLATES.items()
        ]

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
            raise IntelligenceScopeError("Discovery evidence was not found in this organization.")

    def _save(
        self, entity: EntityT, actor_id: UUID, action: str, actor_type: str = "human"
    ) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        mapped = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=mapped.organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=mapped.__tablename__,
            entity_id=cast(UUID, mapped.id),
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
