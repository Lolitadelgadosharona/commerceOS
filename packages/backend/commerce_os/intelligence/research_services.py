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
)
from commerce_os.intelligence.research_schemas import (
    CustomerPainResearchCreate,
    MarketInsightResearchCreate,
    OpportunityResearchBriefCreate,
    ResearchAnalysisCreate,
    ResearchCitationCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

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

    def _save_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=cast(UUID, entity.id),  # type: ignore[attr-defined]
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
