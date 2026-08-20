from typing import TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.research_models import (
    CustomerPainResearch,
    MarketInsightResearch,
    OpportunityResearchBrief,
    ResearchAnalysis,
    ResearchEvidenceCitation,
    ResearchRun,
    ResearchRunEvidence,
)
from commerce_os.intelligence.research_schemas import (
    CustomerPainResearchCreate,
    MarketInsightResearchCreate,
    OpportunityResearchBriefCreate,
    ResearchAnalysisCreate,
    ResearchCitationCreate,
    ResearchRunCreate,
    ResearchTemplateRead,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now

EntityT = TypeVar("EntityT", bound=Base)
ANALYSIS_TRANSITIONS = {
    "draft": {"in_review", "cancelled"},
    "in_review": {"reviewed", "rejected", "cancelled"},
    "reviewed": set(),
    "rejected": set(),
    "cancelled": set(),
}
EVIDENCE_TABLES = {
    "market_data_record": "market_data_records",
    "marketplace_review": "marketplace_review_evidence",
    "normalized_marketplace_review": "normalized_marketplace_reviews",
    "customer_signal": "customer_signals",
    "pain_cluster": "customer_pain_clusters",
    "market_signal": "market_signals",
    "competitive_observation": "competitive_marketplace_observations",
    "opportunity_evidence": "opportunity_evidence",
    "customer_language": "customer_language_insights",
    "research_citation": "research_evidence_citations",
}
RUN_EVIDENCE_TABLES = {
    "market_signal": "market_signals",
    "marketplace_review": "marketplace_review_evidence",
    "pain_cluster": "customer_pain_clusters",
    "customer_language": "customer_language_insights",
    "opportunity_evidence": "opportunity_evidence",
    "research_citation": "research_evidence_citations",
}
RESEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "summary",
        "key_findings",
        "evidence_used",
        "customer_language",
        "confidence",
        "risks",
        "unanswered_questions",
    ],
    "properties": {
        "summary": {"type": "string"},
        "key_findings": {"type": "array"},
        "evidence_used": {"type": "array"},
        "customer_language": {"type": "array"},
        "confidence": {"type": "number"},
        "risks": {"type": "array"},
        "unanswered_questions": {"type": "array"},
    },
}
RESEARCH_TEMPLATES = {
    "product_opportunity_discovery": (
        "Find evidence-backed customer problems and opportunity candidates.",
        ["market_signal", "marketplace_review", "pain_cluster"],
        "candidate",
    ),
    "customer_pain_analysis": (
        "Analyze supplied customer pain and language evidence.",
        ["marketplace_review", "pain_cluster", "customer_language"],
        "analysis",
    ),
    "market_trend_analysis": (
        "Analyze existing market signals without creating opportunities.",
        ["market_signal"],
        "analysis",
    ),
    "competitor_research": (
        "Analyze supplied competitive marketplace evidence.",
        ["marketplace_review", "research_citation"],
        "analysis",
    ),
    "geo_content_research": (
        "Identify evidence-backed customer questions and answer gaps.",
        ["customer_language", "opportunity_evidence"],
        "draft",
    ),
}
RUN_TRANSITIONS = {
    "draft": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


def scoped_research(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError("Research record was not found in this organization.")
    return entity


class ResearchAnalystService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_analysis(self, payload: ResearchAnalysisCreate, actor_id: UUID) -> ResearchAnalysis:
        request = scoped_research(
            self.session, AIRequest, payload.ai_request_id, payload.organization_id
        )
        if str(request.status) in {"failed", "cancelled"}:
            raise IntelligenceValidationError(
                "Research cannot use a failed or cancelled AI request."
            )
        return self._save_audited(
            ResearchAnalysis(**payload.model_dump(), status="draft", reviewed_by=None),
            actor_id,
            "research.analysis.created",
        )

    def create_run(self, payload: ResearchRunCreate, actor_id: UUID) -> ResearchRun:
        if payload.project_id is not None:
            self._reference("projects", payload.project_id, payload.organization_id)
        self._reference("ai_model_capabilities", payload.capability_id, payload.organization_id)
        if payload.prompt_version_id is not None:
            self._reference("prompt_versions", payload.prompt_version_id, payload.organization_id)
        run = ResearchRun(
            **payload.model_dump(exclude={"evidence"}),
            status="draft",
            created_by=actor_id,
            ai_request_id=None,
            analysis_id=None,
            decision_queue_item_id=None,
            started_at=None,
            completed_at=None,
            failure_reason=None,
        )
        self.session.add(run)
        self.session.flush()
        for item in payload.evidence:
            self._reference(
                RUN_EVIDENCE_TABLES[item.evidence_type],
                item.evidence_id,
                payload.organization_id,
            )
            self.session.add(
                ResearchRunEvidence(
                    organization_id=payload.organization_id,
                    research_run_id=run.id,
                    **item.model_dump(),
                )
            )
        return self._commit_audited(run, actor_id, "research.run.created")

    def queue_run(self, run: ResearchRun, actor_id: UUID) -> ResearchRun:
        if run.status != "draft":
            raise IntelligenceValidationError("Only draft research runs may be queued.")
        evidence_types = {
            evidence.evidence_type
            for evidence in self.session.scalars(
                select(ResearchRunEvidence).where(ResearchRunEvidence.research_run_id == run.id)
            )
        }
        if not evidence_types:
            raise IntelligenceValidationError(
                "Research requires evidence references; missing_evidence must not be fabricated."
            )
        allowed_types = set(RESEARCH_TEMPLATES[run.research_type][1])
        if not evidence_types.intersection(allowed_types):
            raise IntelligenceValidationError(
                "Research evidence does not satisfy the selected template requirements."
            )
        run.status = "queued"
        return self._save_audited(run, actor_id, "research.run.queued")

    def cancel_run(self, run: ResearchRun, actor_id: UUID) -> ResearchRun:
        if "cancelled" not in RUN_TRANSITIONS[run.status]:
            raise IntelligenceValidationError(
                "Only draft or queued research runs may be cancelled."
            )
        run.status = "cancelled"
        run.completed_at = utc_now()
        return self._save_audited(run, actor_id, "research.run.cancelled")

    def start_run(self, run: ResearchRun, ai_request_id: UUID, actor_id: UUID) -> ResearchRun:
        if run.status != "queued":
            raise IntelligenceValidationError("Only queued research runs may start.")
        request = scoped_research(self.session, AIRequest, ai_request_id, run.organization_id)
        run.ai_request_id = request.id
        run.status = "running"
        run.started_at = utc_now()
        return self._save_audited(run, actor_id, "research.run.started", actor_type="service")

    def complete_run(self, run: ResearchRun, analysis_id: UUID, actor_id: UUID) -> ResearchRun:
        if run.status != "running":
            raise IntelligenceValidationError("Only running research may complete.")
        analysis = scoped_research(self.session, ResearchAnalysis, analysis_id, run.organization_id)
        run.analysis_id = analysis.id
        run.status = "completed"
        run.completed_at = utc_now()
        return self._save_audited(run, actor_id, "research.run.completed", actor_type="service")

    def fail_run(self, run: ResearchRun, reason: str, actor_id: UUID) -> ResearchRun:
        if run.status != "running":
            raise IntelligenceValidationError("Only running research may fail.")
        run.status = "failed"
        run.failure_reason = reason
        run.completed_at = utc_now()
        return self._save_audited(run, actor_id, "research.run.failed", actor_type="service")

    def attach_decision_queue(
        self, run: ResearchRun, queue_id: UUID, actor_id: UUID
    ) -> ResearchRun:
        if run.status != "completed":
            raise IntelligenceValidationError("Only completed research may request human review.")
        run.decision_queue_item_id = queue_id
        return self._save_audited(run, actor_id, "research.run.review_queued")

    def run_evidence(self, run_id: UUID, organization_id: UUID) -> list[ResearchRunEvidence]:
        scoped_research(self.session, ResearchRun, run_id, organization_id)
        return list(
            self.session.scalars(
                select(ResearchRunEvidence).where(ResearchRunEvidence.research_run_id == run_id)
            )
        )

    @staticmethod
    def templates() -> list[ResearchTemplateRead]:
        return [
            ResearchTemplateRead(
                research_type=research_type,
                goal=values[0],
                evidence_requirements=values[1],
                output_classification=values[2],
                expected_output_schema=RESEARCH_OUTPUT_SCHEMA,
            )
            for research_type, values in RESEARCH_TEMPLATES.items()
        ]

    def transition_analysis(
        self,
        analysis: ResearchAnalysis,
        status: str,
        actor_id: UUID,
    ) -> ResearchAnalysis:
        if status not in ANALYSIS_TRANSITIONS[analysis.status]:
            raise IntelligenceValidationError(
                f"Analysis cannot transition from {analysis.status} to {status}."
            )
        if status == "in_review" and self._citation_count(analysis.id) == 0:
            raise IntelligenceValidationError(
                "Analysis review requires at least one evidence citation."
            )
        analysis.status = status
        if status in {"reviewed", "rejected"}:
            analysis.reviewed_by = actor_id
        return self._save_audited(analysis, actor_id, f"research.analysis.{status}")

    def add_citation(
        self, payload: ResearchCitationCreate, actor_id: UUID
    ) -> ResearchEvidenceCitation:
        analysis = scoped_research(
            self.session, ResearchAnalysis, payload.analysis_id, payload.organization_id
        )
        if analysis.status != "draft":
            raise IntelligenceValidationError("Citations can only be added to draft analyses.")
        table = Base.metadata.tables[EVIDENCE_TABLES[payload.evidence_type]]
        evidence = self.session.scalar(
            select(table.c.id).where(
                table.c.id == payload.evidence_id,
                table.c.organization_id == payload.organization_id,
            )
        )
        if evidence is None:
            raise IntelligenceScopeError("Cited evidence was not found in this organization.")
        return self._save_audited(
            ResearchEvidenceCitation(**payload.model_dump()),
            actor_id,
            "research.citation.created",
        )

    def create_customer_pain(
        self, payload: CustomerPainResearchCreate, actor_id: UUID
    ) -> CustomerPainResearch:
        self._analysis_with_citations(payload.analysis_id, payload.organization_id, "customer_pain")
        return self._save_audited(
            CustomerPainResearch(**payload.model_dump()), actor_id, "research.customer_pain.created"
        )

    def create_market_insight(
        self, payload: MarketInsightResearchCreate, actor_id: UUID
    ) -> MarketInsightResearch:
        self._analysis_with_citations(
            payload.analysis_id, payload.organization_id, "market_insight"
        )
        return self._save_audited(
            MarketInsightResearch(**payload.model_dump()),
            actor_id,
            "research.market_insight.created",
        )

    def create_brief(
        self, payload: OpportunityResearchBriefCreate, actor_id: UUID
    ) -> OpportunityResearchBrief:
        self._analysis_with_citations(
            payload.analysis_id, payload.organization_id, "opportunity_brief"
        )
        opportunities = Base.metadata.tables["market_opportunities"]
        exists = self.session.scalar(
            select(opportunities.c.id).where(
                opportunities.c.id == payload.opportunity_id,
                opportunities.c.organization_id == payload.organization_id,
            )
        )
        if exists is None:
            raise IntelligenceScopeError("Existing opportunity was not found in this organization.")
        return self._save_audited(
            OpportunityResearchBrief(**payload.model_dump()),
            actor_id,
            "research.opportunity_brief.created",
        )

    def _analysis_with_citations(
        self, analysis_id: UUID, organization_id: UUID, expected_type: str
    ) -> ResearchAnalysis:
        analysis = scoped_research(self.session, ResearchAnalysis, analysis_id, organization_id)
        if analysis.analysis_type != expected_type:
            raise IntelligenceValidationError(
                f"Analysis type must be {expected_type} for this research record."
            )
        if self._citation_count(analysis.id) == 0:
            raise IntelligenceValidationError("Structured research requires evidence citations.")
        return analysis

    def _citation_count(self, analysis_id: UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(ResearchEvidenceCitation)
                .where(ResearchEvidenceCitation.analysis_id == analysis_id)
            )
            or 0
        )

    def _run_evidence_count(self, run_id: UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(ResearchRunEvidence)
                .where(ResearchRunEvidence.research_run_id == run_id)
            )
            or 0
        )

    def _reference(self, table_name: str, entity_id: UUID, organization_id: UUID) -> None:
        table = Base.metadata.tables[table_name]
        exists = self.session.scalar(
            select(table.c.id).where(
                table.c.id == entity_id, table.c.organization_id == organization_id
            )
        )
        if exists is None:
            raise IntelligenceScopeError("Evidence reference was not found in this organization.")

    def _commit_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        return self._save_audited(entity, actor_id, action)

    def _save_audited(
        self, entity: EntityT, actor_id: UUID, action: str, actor_type: str = "human"
    ) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=cast(UUID, entity.id),  # type: ignore[attr-defined]
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
