from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.ai_runtime.models import AICostObservation, AIRequest
from commerce_os.governance.executive_schemas import DecisionQueueCreate
from commerce_os.governance.executive_services import DecisionQueueService
from commerce_os.intelligence.research_models import (
    CustomerPainResearch,
    MarketInsightResearch,
    OpportunityResearchBrief,
    ResearchAnalysis,
    ResearchEvidenceCitation,
    ResearchRun,
)
from commerce_os.intelligence.research_schemas import (
    CustomerPainResearchCreate,
    CustomerPainResearchRead,
    MarketInsightResearchCreate,
    MarketInsightResearchRead,
    OpportunityResearchBriefCreate,
    OpportunityResearchBriefRead,
    ResearchAnalysisCreate,
    ResearchAnalysisRead,
    ResearchAnalysisTransition,
    ResearchCitationCreate,
    ResearchCitationRead,
    ResearchRunCreate,
    ResearchRunRead,
    ResearchRunResult,
    ResearchTemplateRead,
)
from commerce_os.intelligence.research_services import ResearchAnalystService, scoped_research
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.market_connector_routes import initiating_actor

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def actor_id(request: Request) -> UUID:
    actor = initiating_actor(request)
    if actor is None:
        raise ApiError(401, "actor_required", "Verified actor identity is required.")
    return actor


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/research-analyses", response_model=ResearchAnalysisRead, status_code=201)
def create_analysis(
    payload: ResearchAnalysisCreate, request: Request, session: SessionDependency
) -> ResearchAnalysis:
    return ResearchAnalystService(session).create_analysis(payload, actor_id(request))


@router.get("/research-analyses", response_model=list[ResearchAnalysisRead])
def list_analyses(organization_id: UUID, session: SessionDependency) -> list[ResearchAnalysis]:
    return _list(session, ResearchAnalysis, organization_id)


@router.patch("/research-analyses/{analysis_id}", response_model=ResearchAnalysisRead)
def transition_analysis(
    analysis_id: UUID,
    organization_id: UUID,
    payload: ResearchAnalysisTransition,
    request: Request,
    session: SessionDependency,
) -> ResearchAnalysis:
    analysis = scoped_research(session, ResearchAnalysis, analysis_id, organization_id)
    return ResearchAnalystService(session).transition_analysis(
        analysis, payload.status, actor_id(request)
    )


@router.post("/research-citations", response_model=ResearchCitationRead, status_code=201)
def add_citation(
    payload: ResearchCitationCreate, request: Request, session: SessionDependency
) -> ResearchEvidenceCitation:
    return ResearchAnalystService(session).add_citation(payload, actor_id(request))


@router.get("/research-citations", response_model=list[ResearchCitationRead])
def list_citations(
    organization_id: UUID, session: SessionDependency
) -> list[ResearchEvidenceCitation]:
    return _list(session, ResearchEvidenceCitation, organization_id)


@router.post("/customer-pain-research", response_model=CustomerPainResearchRead, status_code=201)
def create_customer_pain(
    payload: CustomerPainResearchCreate, request: Request, session: SessionDependency
) -> CustomerPainResearch:
    return ResearchAnalystService(session).create_customer_pain(payload, actor_id(request))


@router.get("/customer-pain-research", response_model=list[CustomerPainResearchRead])
def list_customer_pain(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerPainResearch]:
    return _list(session, CustomerPainResearch, organization_id)


@router.post("/market-insight-research", response_model=MarketInsightResearchRead, status_code=201)
def create_market_insight(
    payload: MarketInsightResearchCreate, request: Request, session: SessionDependency
) -> MarketInsightResearch:
    return ResearchAnalystService(session).create_market_insight(payload, actor_id(request))


@router.get("/market-insight-research", response_model=list[MarketInsightResearchRead])
def list_market_insights(
    organization_id: UUID, session: SessionDependency
) -> list[MarketInsightResearch]:
    return _list(session, MarketInsightResearch, organization_id)


@router.post(
    "/opportunity-research-briefs", response_model=OpportunityResearchBriefRead, status_code=201
)
def create_brief(
    payload: OpportunityResearchBriefCreate, request: Request, session: SessionDependency
) -> OpportunityResearchBrief:
    return ResearchAnalystService(session).create_brief(payload, actor_id(request))


@router.get("/opportunity-research-briefs", response_model=list[OpportunityResearchBriefRead])
def list_briefs(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityResearchBrief]:
    return _list(session, OpportunityResearchBrief, organization_id)


@router.get("/research-templates", response_model=list[ResearchTemplateRead])
def list_research_templates() -> list[ResearchTemplateRead]:
    return ResearchAnalystService.templates()


@router.post("/research-runs", response_model=ResearchRunRead, status_code=201)
def create_research_run(
    payload: ResearchRunCreate, request: Request, session: SessionDependency
) -> ResearchRun:
    return ResearchAnalystService(session).create_run(payload, actor_id(request))


@router.get("/research-runs", response_model=list[ResearchRunRead])
def list_research_runs(organization_id: UUID, session: SessionDependency) -> list[ResearchRun]:
    return _list(session, ResearchRun, organization_id)


@router.get("/research-runs/{run_id}", response_model=ResearchRunRead)
def get_research_run(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> ResearchRun:
    return scoped_research(session, ResearchRun, run_id, organization_id)


@router.post("/research-runs/{run_id}/queue", response_model=ResearchRunRead)
def queue_research_run(
    run_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> ResearchRun:
    service = ResearchAnalystService(session)
    return service.queue_run(
        scoped_research(session, ResearchRun, run_id, organization_id), actor_id(request)
    )


@router.post("/research-runs/{run_id}/cancel", response_model=ResearchRunRead)
def cancel_research_run(
    run_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> ResearchRun:
    service = ResearchAnalystService(session)
    return service.cancel_run(
        scoped_research(session, ResearchRun, run_id, organization_id), actor_id(request)
    )


@router.get("/research-runs/{run_id}/results", response_model=ResearchRunResult)
def research_run_results(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> ResearchRunResult:
    run = scoped_research(session, ResearchRun, run_id, organization_id)
    analysis = session.get(ResearchAnalysis, run.analysis_id) if run.analysis_id else None
    execution = session.get(AIRequest, run.ai_request_id) if run.ai_request_id else None
    cost = (
        session.scalar(
            select(AICostObservation).where(
                AICostObservation.related_request_id == run.ai_request_id
            )
        )
        if run.ai_request_id
        else None
    )
    return ResearchRunResult(
        run=ResearchRunRead.model_validate(run),
        analysis=ResearchAnalysisRead.model_validate(analysis) if analysis else None,
        execution=(
            {
                "status": str(execution.status),
                "provider": execution.selected_provider_identity,
                "model": execution.selected_model_identity,
                "prompt_version_id": str(execution.prompt_version_id)
                if execution.prompt_version_id
                else None,
                "output_classification": str(execution.output_classification),
                "latency_ms": execution.latency_ms,
            }
            if execution
            else None
        ),
        usage_cost=(
            {
                "estimated_cost": str(cost.estimated_cost),
                "provider_reported_cost": str(cost.provider_reported_cost)
                if cost.provider_reported_cost is not None
                else None,
                "cost_basis": cost.cost_basis,
                "input_tokens": cost.input_tokens,
                "output_tokens": cost.output_tokens,
                "total_tokens": cost.total_tokens,
            }
            if cost
            else None
        ),
    )


@router.post("/research-runs/{run_id}/decision-queue", response_model=ResearchRunRead)
def queue_research_review(
    run_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> ResearchRun:
    service = ResearchAnalystService(session)
    run = scoped_research(session, ResearchRun, run_id, organization_id)
    if run.status != "completed":
        raise ApiError(
            409,
            "research_not_completed",
            "Only completed research may enter the decision queue.",
        )
    if run.decision_queue_item_id is not None:
        raise ApiError(
            409,
            "research_review_already_queued",
            "Research already has a decision queue review.",
        )
    queue = DecisionQueueService(session).create(
        DecisionQueueCreate(
            organization_id=organization_id,
            title=f"Review research: {run.research_type}",
            domain="intelligence",
            reason=run.objective,
            priority="high",
            required_action="review",
        )
    )
    return service.attach_decision_queue(run, queue.id, actor_id(request))
