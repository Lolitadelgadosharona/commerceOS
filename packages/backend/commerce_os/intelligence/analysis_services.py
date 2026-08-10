from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.intelligence.analysis_models import (
    MarketSignalAnalysis,
    OpportunityAssessment,
    OpportunityReport,
)
from commerce_os.intelligence.analysis_schemas import (
    OpportunityAssessmentCreate,
    OpportunityReportCreate,
    SignalAnalysisCreate,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
REPORT_TRANSITIONS = {"draft": {"review"}, "review": {"presented"}, "presented": set()}
ASSESSMENT_FORMULA = "opportunity-assessment-v1.0"


def scoped_analysis(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Opportunity analysis record was not found in this organization."
        )
    return entity


class OpportunityAnalysisService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def analyze_signal(self, payload: SignalAnalysisCreate) -> MarketSignalAnalysis:
        self._reference(
            "market_signals", payload.signal_id, payload.organization_id, "Market signal"
        )
        return self._save(MarketSignalAnalysis(**payload.model_dump()))

    def assess(self, payload: OpportunityAssessmentCreate) -> OpportunityAssessment:
        self._reference(
            "market_opportunities",
            payload.market_opportunity_id,
            payload.organization_id,
            "Market opportunity",
        )
        evidence_links = self.session.scalar(
            select(func.count())
            .select_from(Base.metadata.tables["market_signal_opportunity_links"])
            .where(
                Base.metadata.tables["market_signal_opportunity_links"].c.opportunity_id
                == payload.market_opportunity_id,
                Base.metadata.tables["market_signal_opportunity_links"].c.organization_id
                == payload.organization_id,
            )
        )
        if not evidence_links:
            raise IntelligenceValidationError(
                "Opportunity assessment requires at least one linked market signal."
            )
        overall = round(
            payload.demand_score * 0.25
            + payload.timing_score * 0.20
            + payload.evidence_score * 0.20
            + (100 - payload.risk_score) * 0.10
            + payload.commercial_score * 0.25,
            2,
        )
        return self._save(
            OpportunityAssessment(
                **payload.model_dump(), overall_score=overall, formula_version=ASSESSMENT_FORMULA
            )
        )

    def create_report(self, payload: OpportunityReportCreate) -> OpportunityReport:
        self._reference(
            "market_opportunities", payload.opportunity_id, payload.organization_id, "Opportunity"
        )
        assessments = Base.metadata.tables["opportunity_assessments"]
        exists = self.session.execute(
            select(assessments.c.id).where(
                assessments.c.market_opportunity_id == payload.opportunity_id,
                assessments.c.organization_id == payload.organization_id,
            )
        ).first()
        if exists is None:
            raise IntelligenceValidationError(
                "Opportunity report requires a structured opportunity assessment."
            )
        return self._save(
            OpportunityReport(**payload.model_dump(), status="draft", decision_queue_item_id=None)
        )

    def transition_report(self, report: OpportunityReport, status: str) -> OpportunityReport:
        if status not in REPORT_TRANSITIONS[report.status]:
            raise IntelligenceValidationError(
                f"Opportunity report cannot transition from {report.status} to {status}."
            )
        report.status = status
        return self._save(report)

    def link_queue(self, report: OpportunityReport, queue_item_id: UUID) -> OpportunityReport:
        self._reference(
            "decision_queue_items", queue_item_id, report.organization_id, "Decision queue item"
        )
        if report.decision_queue_item_id is not None:
            raise IntelligenceValidationError(
                "Opportunity report already has a decision queue link."
            )
        report.decision_queue_item_id = queue_item_id
        return self._save(report)

    def _reference(self, table: str, reference_id: UUID, organization_id: UUID, label: str) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name=table,
            reference_id=reference_id,
            organization_id=organization_id,
        ):
            raise IntelligenceScopeError(f"{label} was not found in this organization.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
