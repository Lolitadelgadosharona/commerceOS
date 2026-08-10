from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.intelligence.analysis_models import (
    MarketSignalAnalysis,
    OpportunityAssessment,
    OpportunityReport,
)
from commerce_os.intelligence.analysis_schemas import (
    OpportunityAssessmentCreate,
    OpportunityAssessmentRead,
    OpportunityReportCreate,
    OpportunityReportRead,
    OpportunityReportUpdate,
    ReportQueueCreate,
    SignalAnalysisCreate,
    SignalAnalysisRead,
)
from commerce_os.intelligence.analysis_services import OpportunityAnalysisService, scoped_analysis
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped_model = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped_model.organization_id == organization_id)
            .order_by(mapped_model.created_at.desc())
        )
    )


@router.post("/signal-analysis", response_model=SignalAnalysisRead, status_code=201)
def analyze_signal(
    payload: SignalAnalysisCreate, session: SessionDependency
) -> MarketSignalAnalysis:
    return OpportunityAnalysisService(session).analyze_signal(payload)


@router.get("/signal-analysis", response_model=list[SignalAnalysisRead])
def list_analysis(organization_id: UUID, session: SessionDependency) -> list[MarketSignalAnalysis]:
    return _list(session, MarketSignalAnalysis, organization_id)


@router.post("/opportunity-assessments", response_model=OpportunityAssessmentRead, status_code=201)
def assess_opportunity(
    payload: OpportunityAssessmentCreate, session: SessionDependency
) -> OpportunityAssessment:
    return OpportunityAnalysisService(session).assess(payload)


@router.get("/opportunity-assessments", response_model=list[OpportunityAssessmentRead])
def list_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityAssessment]:
    return _list(session, OpportunityAssessment, organization_id)


@router.post("/opportunity-reports", response_model=OpportunityReportRead, status_code=201)
def create_report(
    payload: OpportunityReportCreate, session: SessionDependency
) -> OpportunityReport:
    return OpportunityAnalysisService(session).create_report(payload)


@router.get("/opportunity-reports", response_model=list[OpportunityReportRead])
def list_reports(organization_id: UUID, session: SessionDependency) -> list[OpportunityReport]:
    return _list(session, OpportunityReport, organization_id)


@router.patch("/opportunity-reports/{report_id}", response_model=OpportunityReportRead)
def transition_report(
    report_id: UUID,
    organization_id: UUID,
    payload: OpportunityReportUpdate,
    session: SessionDependency,
) -> OpportunityReport:
    report = scoped_analysis(session, OpportunityReport, report_id, organization_id)
    return OpportunityAnalysisService(session).transition_report(report, payload.status)


@router.post(
    "/opportunity-reports/{report_id}/decision-queue",
    response_model=OpportunityReportRead,
    status_code=201,
)
def send_to_decision_queue(
    report_id: UUID, payload: ReportQueueCreate, session: SessionDependency
) -> OpportunityReport:
    report = scoped_analysis(session, OpportunityReport, report_id, payload.organization_id)
    queue = DecisionQueueService(session).create(
        DecisionQueueCreate(
            organization_id=payload.organization_id,
            title=f"Review opportunity report: {report.title}",
            domain="intelligence",
            reason=(
                "Advisory opportunity report requires human review. "
                "This queue item grants no approval or execution authority."
            ),
            priority=payload.priority,
            required_action="review",
        )
    )
    return OpportunityAnalysisService(session).link_queue(report, queue.id)
