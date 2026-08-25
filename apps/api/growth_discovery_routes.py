from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.growth.discovery_models import (
    BusinessProfileEvidenceSnapshot,
    DiscoveryAutomationPlan,
    GoogleBusinessDiscoveryResult,
    GrowthBusinessResearchResult,
    GrowthBusinessResearchRun,
    InstagramEvidenceSnapshot,
    ProspectCandidate,
    ProspectDiscoveryRun,
    ProspectDiscoverySource,
    ProspectMemoryEvent,
    ProspectQualificationAssessment,
    ProspectResearchEvidence,
    WebsiteEvidenceSnapshot,
)
from commerce_os.growth.discovery_schemas import (
    AutomationPlanCreate,
    AutomationPlanRead,
    BusinessDemandSignalRead,
    BusinessProfileEvidenceCreate,
    BusinessProfileEvidenceRead,
    BusinessResearchResultRead,
    BusinessResearchRunRead,
    BusinessResearchStart,
    CandidateRead,
    DiscoveryRunCreate,
    DiscoveryRunRead,
    DiscoverySourceCreate,
    DiscoverySourceRead,
    GoogleBusinessResultCreate,
    GoogleBusinessResultRead,
    InstagramEvidenceCreate,
    InstagramEvidenceRead,
    ManualProspectImport,
    OperatorRevenueDashboard,
    ProspectMemoryEventCreate,
    ProspectMemoryEventRead,
    ProspectPipelineRead,
    QualificationInputs,
    QualificationRead,
    RankedProspectRead,
    ResearchEvidenceCreate,
    ResearchEvidenceRead,
    WebsiteEvidenceCreate,
    WebsiteEvidenceRead,
)
from commerce_os.growth.discovery_services import GrowthDiscoveryService, scoped_growth_discovery
from commerce_os.intelligence.business_signal_models import BusinessDemandSignal
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


@router.post("/prospect-discovery-sources", response_model=DiscoverySourceRead, status_code=201)
def create_source(
    payload: DiscoverySourceCreate, request: Request, session: SessionDependency
) -> ProspectDiscoverySource:
    return GrowthDiscoveryService(session).create_source(payload, actor_id(request))


@router.get("/prospect-discovery-sources", response_model=list[DiscoverySourceRead])
def list_sources(
    organization_id: UUID, session: SessionDependency
) -> list[ProspectDiscoverySource]:
    return _list(session, ProspectDiscoverySource, organization_id)


@router.post("/discovery-automation-plans", response_model=AutomationPlanRead, status_code=201)
def create_automation_plan(
    payload: AutomationPlanCreate, request: Request, session: SessionDependency
) -> DiscoveryAutomationPlan:
    return GrowthDiscoveryService(session).create_automation_plan(payload, actor_id(request))


@router.get("/discovery-automation-plans", response_model=list[AutomationPlanRead])
def list_automation_plans(
    organization_id: UUID, session: SessionDependency
) -> list[DiscoveryAutomationPlan]:
    return _list(session, DiscoveryAutomationPlan, organization_id)


@router.post(
    "/discovery-automation-plans/{plan_id}/runs",
    response_model=DiscoveryRunRead,
    status_code=201,
)
def start_automation_run(
    plan_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ProspectDiscoveryRun:
    plan = scoped_growth_discovery(session, DiscoveryAutomationPlan, plan_id, organization_id)
    return GrowthDiscoveryService(session).start_automation_run(plan, actor_id(request))


@router.post("/prospect-discovery-runs", response_model=DiscoveryRunRead, status_code=201)
def create_run(
    payload: DiscoveryRunCreate, request: Request, session: SessionDependency
) -> ProspectDiscoveryRun:
    return GrowthDiscoveryService(session).create_run(payload, actor_id(request))


@router.get("/prospect-discovery-runs", response_model=list[DiscoveryRunRead])
def list_runs(organization_id: UUID, session: SessionDependency) -> list[ProspectDiscoveryRun]:
    return _list(session, ProspectDiscoveryRun, organization_id)


@router.get("/prospect-discovery-runs/{run_id}", response_model=DiscoveryRunRead)
def get_run(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProspectDiscoveryRun:
    return scoped_growth_discovery(session, ProspectDiscoveryRun, run_id, organization_id)


@router.post("/prospect-discovery-runs/{run_id}/queue", response_model=DiscoveryRunRead)
def queue_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ProspectDiscoveryRun:
    service = GrowthDiscoveryService(session)
    return service.transition_run(
        scoped_growth_discovery(session, ProspectDiscoveryRun, run_id, organization_id),
        "queued",
        actor_id(request),
    )


@router.post("/prospect-discovery-runs/{run_id}/cancel", response_model=DiscoveryRunRead)
def cancel_run(
    run_id: UUID, organization_id: UUID, request: Request, session: SessionDependency
) -> ProspectDiscoveryRun:
    service = GrowthDiscoveryService(session)
    return service.transition_run(
        scoped_growth_discovery(session, ProspectDiscoveryRun, run_id, organization_id),
        "cancelled",
        actor_id(request),
    )


@router.get("/prospect-candidates", response_model=list[CandidateRead])
def list_candidates(organization_id: UUID, session: SessionDependency) -> list[ProspectCandidate]:
    return _list(session, ProspectCandidate, organization_id)


@router.post("/growth-prospect-imports", response_model=CandidateRead, status_code=201)
def import_manual_prospect(
    payload: ManualProspectImport, request: Request, session: SessionDependency
) -> ProspectCandidate:
    return GrowthDiscoveryService(session).import_manual_prospect(payload, actor_id(request))


@router.post("/google-business-results", response_model=GoogleBusinessResultRead, status_code=201)
def record_google_business_result(
    payload: GoogleBusinessResultCreate, request: Request, session: SessionDependency
) -> GoogleBusinessDiscoveryResult:
    return GrowthDiscoveryService(session).record_google_business_result(payload, actor_id(request))


@router.get("/google-business-results", response_model=list[GoogleBusinessResultRead])
def list_google_business_results(
    organization_id: UUID, session: SessionDependency
) -> list[GoogleBusinessDiscoveryResult]:
    return _list(session, GoogleBusinessDiscoveryResult, organization_id)


@router.post("/prospect-memory", response_model=ProspectMemoryEventRead, status_code=201)
def record_prospect_memory(
    payload: ProspectMemoryEventCreate, request: Request, session: SessionDependency
) -> ProspectMemoryEvent:
    return GrowthDiscoveryService(session).record_memory_event(payload, actor_id(request))


@router.get("/prospect-memory", response_model=list[ProspectMemoryEventRead])
def list_prospect_memory(
    organization_id: UUID, session: SessionDependency
) -> list[ProspectMemoryEvent]:
    return _list(session, ProspectMemoryEvent, organization_id)


@router.get("/ranked-prospects", response_model=list[RankedProspectRead])
def ranked_prospects(organization_id: UUID, session: SessionDependency) -> list[RankedProspectRead]:
    return GrowthDiscoveryService(session).ranked_prospects(organization_id)


@router.get("/prospect-candidates/{candidate_id}", response_model=CandidateRead)
def get_candidate(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProspectCandidate:
    return scoped_growth_discovery(session, ProspectCandidate, candidate_id, organization_id)


@router.post("/prospect-research-evidence", response_model=ResearchEvidenceRead, status_code=201)
def create_evidence(
    payload: ResearchEvidenceCreate, request: Request, session: SessionDependency
) -> ProspectResearchEvidence:
    return GrowthDiscoveryService(session).create_evidence(payload, actor_id(request))


@router.get("/prospect-research-evidence", response_model=list[ResearchEvidenceRead])
def list_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[ProspectResearchEvidence]:
    return _list(session, ProspectResearchEvidence, organization_id)


@router.post("/website-evidence", response_model=WebsiteEvidenceRead, status_code=201)
def collect_website_evidence(
    payload: WebsiteEvidenceCreate, request: Request, session: SessionDependency
) -> WebsiteEvidenceSnapshot:
    return GrowthDiscoveryService(session).collect_website_evidence(payload, actor_id(request))


@router.get("/website-evidence", response_model=list[WebsiteEvidenceRead])
def list_website_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[WebsiteEvidenceSnapshot]:
    return _list(session, WebsiteEvidenceSnapshot, organization_id)


@router.post(
    "/business-profile-evidence", response_model=BusinessProfileEvidenceRead, status_code=201
)
def collect_business_profile_evidence(
    payload: BusinessProfileEvidenceCreate, request: Request, session: SessionDependency
) -> BusinessProfileEvidenceSnapshot:
    return GrowthDiscoveryService(session).collect_business_profile_evidence(
        payload, actor_id(request)
    )


@router.get("/business-profile-evidence", response_model=list[BusinessProfileEvidenceRead])
def list_business_profile_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[BusinessProfileEvidenceSnapshot]:
    return _list(session, BusinessProfileEvidenceSnapshot, organization_id)


@router.post("/instagram-evidence", response_model=InstagramEvidenceRead, status_code=201)
def collect_instagram_evidence(
    payload: InstagramEvidenceCreate, request: Request, session: SessionDependency
) -> InstagramEvidenceSnapshot:
    return GrowthDiscoveryService(session).collect_instagram_evidence(payload, actor_id(request))


@router.get("/instagram-evidence", response_model=list[InstagramEvidenceRead])
def list_instagram_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[InstagramEvidenceSnapshot]:
    return _list(session, InstagramEvidenceSnapshot, organization_id)


@router.get("/prospect-candidates/{candidate_id}/pipeline", response_model=ProspectPipelineRead)
def prospect_pipeline(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProspectPipelineRead:
    return GrowthDiscoveryService(session).pipeline(candidate_id, organization_id)


@router.get("/operator-revenue-dashboard", response_model=OperatorRevenueDashboard)
def operator_revenue_dashboard(
    organization_id: UUID, session: SessionDependency
) -> OperatorRevenueDashboard:
    return GrowthDiscoveryService(session).operator_dashboard(organization_id)


@router.post(
    "/prospect-candidates/{candidate_id}/research",
    response_model=BusinessResearchRunRead,
    status_code=201,
)
def start_research(
    candidate_id: UUID,
    payload: BusinessResearchStart,
    request: Request,
    session: SessionDependency,
) -> GrowthBusinessResearchRun:
    candidate = scoped_growth_discovery(
        session, ProspectCandidate, candidate_id, payload.organization_id
    )
    return GrowthDiscoveryService(session).create_research_run(
        candidate, payload, actor_id(request)
    )


@router.get("/growth-business-research-runs", response_model=list[BusinessResearchRunRead])
def list_research_runs(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthBusinessResearchRun]:
    return _list(session, GrowthBusinessResearchRun, organization_id)


@router.get(
    "/growth-business-research-runs/{run_id}/results",
    response_model=BusinessResearchResultRead | None,
)
def research_results(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> GrowthBusinessResearchResult | None:
    scoped_growth_discovery(session, GrowthBusinessResearchRun, run_id, organization_id)
    return session.scalar(
        select(GrowthBusinessResearchResult).where(
            GrowthBusinessResearchResult.organization_id == organization_id,
            GrowthBusinessResearchResult.research_run_id == run_id,
        )
    )


@router.post(
    "/prospect-candidates/{candidate_id}/qualification",
    response_model=QualificationRead,
)
def calculate_qualification(
    candidate_id: UUID,
    payload: QualificationInputs,
    request: Request,
    session: SessionDependency,
) -> ProspectQualificationAssessment:
    candidate = scoped_growth_discovery(
        session, ProspectCandidate, candidate_id, payload.organization_id
    )
    return GrowthDiscoveryService(session).qualify(candidate, payload, actor_id(request))


@router.get(
    "/prospect-candidates/{candidate_id}/qualification", response_model=QualificationRead | None
)
def qualification(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProspectQualificationAssessment | None:
    scoped_growth_discovery(session, ProspectCandidate, candidate_id, organization_id)
    return session.scalar(
        select(ProspectQualificationAssessment).where(
            ProspectQualificationAssessment.organization_id == organization_id,
            ProspectQualificationAssessment.candidate_id == candidate_id,
        )
    )


@router.get("/business-demand-signals", response_model=list[BusinessDemandSignalRead])
def business_signals(
    organization_id: UUID, session: SessionDependency
) -> list[BusinessDemandSignal]:
    return _list(session, BusinessDemandSignal, organization_id)


@router.get("/growth-business-research-runs/{run_id}/ai-request")
def research_ai_request(
    run_id: UUID, organization_id: UUID, session: SessionDependency
) -> dict[str, object] | None:
    run = scoped_growth_discovery(session, GrowthBusinessResearchRun, run_id, organization_id)
    request = session.get(AIRequest, run.ai_request_id) if run.ai_request_id else None
    if request is None:
        return None
    return {
        "id": request.id,
        "status": str(request.status),
        "provider": request.selected_provider_identity,
        "model": request.selected_model_identity,
        "task_type": request.task_type,
        "authority": "advisory_only",
    }
