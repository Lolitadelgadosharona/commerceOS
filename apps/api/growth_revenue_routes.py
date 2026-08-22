from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.growth.activation_models import (
    OutreachTrackingEvent,
    RevenueExperiment,
)
from commerce_os.growth.discovery_models import (
    GrowthBusinessResearchResult,
    GrowthBusinessResearchRun,
    ProspectCandidate,
    ProspectQualificationAssessment,
)
from commerce_os.growth.revenue_models import (
    AIModelPolicy,
    BusinessGrowthProfile,
    GrowthGift,
    GrowthOpportunityAnalysis,
    GrowthOutreachDraft,
    GrowthProspect,
    GrowthProspectEvidence,
    GrowthProspectRanking,
    SalesConversationAnalysis,
)
from commerce_os.growth.revenue_schemas import (
    AIModelPolicyCreate,
    AIModelPolicyRead,
    BusinessGrowthProfileCreate,
    BusinessGrowthProfileRead,
    GrowthDashboardRead,
    GrowthGiftCreate,
    GrowthGiftRead,
    GrowthRevenueV2Dashboard,
    OpportunityAnalysisCreate,
    OpportunityAnalysisRead,
    OutreachDraftCreate,
    OutreachDraftRead,
    ProspectCreate,
    ProspectEvidenceCreate,
    ProspectEvidenceRead,
    ProspectRankingCreate,
    ProspectRankingRead,
    ProspectRead,
    ProspectTransition,
    SalesAnalysisCreate,
    SalesAnalysisRead,
    StatusTransition,
)
from commerce_os.growth.revenue_services import GrowthRevenueService, scoped_revenue
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
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


@router.post("/growth-prospects", response_model=ProspectRead, status_code=201)
def create_prospect(
    payload: ProspectCreate, request: Request, session: SessionDependency
) -> GrowthProspect:
    return GrowthRevenueService(session).create_prospect(payload, actor_id(request))


@router.get("/growth-prospects", response_model=list[ProspectRead])
def list_prospects(organization_id: UUID, session: SessionDependency) -> list[GrowthProspect]:
    return _list(session, GrowthProspect, organization_id)


@router.patch("/growth-prospects/{entity_id}", response_model=ProspectRead)
def transition_prospect(
    entity_id: UUID,
    organization_id: UUID,
    payload: ProspectTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthProspect:
    entity = scoped_revenue(session, GrowthProspect, entity_id, organization_id)
    return GrowthRevenueService(session).transition_prospect(
        entity, payload.status, actor_id(request)
    )


@router.post("/growth-prospect-evidence", response_model=ProspectEvidenceRead, status_code=201)
def create_evidence(
    payload: ProspectEvidenceCreate, request: Request, session: SessionDependency
) -> GrowthProspectEvidence:
    return GrowthRevenueService(session).create_evidence(payload, actor_id(request))


@router.get("/growth-prospect-evidence", response_model=list[ProspectEvidenceRead])
def list_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthProspectEvidence]:
    return _list(session, GrowthProspectEvidence, organization_id)


@router.post("/business-growth-profiles", response_model=BusinessGrowthProfileRead, status_code=201)
def create_business_growth_profile(
    payload: BusinessGrowthProfileCreate, request: Request, session: SessionDependency
) -> BusinessGrowthProfile:
    return GrowthRevenueService(session).create_business_profile(payload, actor_id(request))


@router.get("/business-growth-profiles", response_model=list[BusinessGrowthProfileRead])
def list_business_growth_profiles(
    organization_id: UUID, session: SessionDependency
) -> list[BusinessGrowthProfile]:
    return _list(session, BusinessGrowthProfile, organization_id)


@router.post("/growth-prospect-rankings", response_model=ProspectRankingRead)
def rank_growth_prospect(
    payload: ProspectRankingCreate, request: Request, session: SessionDependency
) -> GrowthProspectRanking:
    return GrowthRevenueService(session).rank_prospect(payload, actor_id(request))


@router.get("/growth-prospect-rankings", response_model=list[ProspectRankingRead])
def list_growth_prospect_rankings(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthProspectRanking]:
    return _list(session, GrowthProspectRanking, organization_id)


@router.post(
    "/growth-opportunity-analyses", response_model=OpportunityAnalysisRead, status_code=201
)
def create_opportunity(
    payload: OpportunityAnalysisCreate, request: Request, session: SessionDependency
) -> GrowthOpportunityAnalysis:
    return GrowthRevenueService(session).create_opportunity(payload, actor_id(request))


@router.get("/growth-opportunity-analyses", response_model=list[OpportunityAnalysisRead])
def list_opportunities(
    organization_id: UUID, session: SessionDependency
) -> list[GrowthOpportunityAnalysis]:
    return _list(session, GrowthOpportunityAnalysis, organization_id)


@router.post("/growth-gifts", response_model=GrowthGiftRead, status_code=201)
def create_gift(
    payload: GrowthGiftCreate, request: Request, session: SessionDependency
) -> GrowthGift:
    return GrowthRevenueService(session).create_gift(payload, actor_id(request))


@router.get("/growth-gifts", response_model=list[GrowthGiftRead])
def list_gifts(organization_id: UUID, session: SessionDependency) -> list[GrowthGift]:
    return _list(session, GrowthGift, organization_id)


@router.patch("/growth-gifts/{entity_id}", response_model=GrowthGiftRead)
def transition_gift(
    entity_id: UUID,
    organization_id: UUID,
    payload: StatusTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthGift:
    return GrowthRevenueService(session).transition_gift(
        scoped_revenue(session, GrowthGift, entity_id, organization_id),
        payload.status,
        actor_id(request),
        payload.approval_request_id,
    )


@router.post("/growth-outreach-drafts", response_model=OutreachDraftRead, status_code=201)
def create_outreach(
    payload: OutreachDraftCreate, request: Request, session: SessionDependency
) -> GrowthOutreachDraft:
    return GrowthRevenueService(session).create_outreach(payload, actor_id(request))


@router.get("/growth-outreach-drafts", response_model=list[OutreachDraftRead])
def list_outreach(organization_id: UUID, session: SessionDependency) -> list[GrowthOutreachDraft]:
    return _list(session, GrowthOutreachDraft, organization_id)


@router.patch("/growth-outreach-drafts/{entity_id}", response_model=OutreachDraftRead)
def transition_outreach(
    entity_id: UUID,
    organization_id: UUID,
    payload: StatusTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthOutreachDraft:
    return GrowthRevenueService(session).transition_outreach(
        scoped_revenue(session, GrowthOutreachDraft, entity_id, organization_id),
        payload.status,
        actor_id(request),
        payload.approval_request_id,
    )


@router.post("/sales-conversation-analyses", response_model=SalesAnalysisRead, status_code=201)
def create_sales_analysis(
    payload: SalesAnalysisCreate, request: Request, session: SessionDependency
) -> SalesConversationAnalysis:
    return GrowthRevenueService(session).create_sales_analysis(payload, actor_id(request))


@router.get("/sales-conversation-analyses", response_model=list[SalesAnalysisRead])
def list_sales_analyses(
    organization_id: UUID, session: SessionDependency
) -> list[SalesConversationAnalysis]:
    return _list(session, SalesConversationAnalysis, organization_id)


@router.post("/ai-model-policies", response_model=AIModelPolicyRead, status_code=201)
def create_model_policy(
    payload: AIModelPolicyCreate, request: Request, session: SessionDependency
) -> AIModelPolicy:
    return GrowthRevenueService(session).create_model_policy(payload, actor_id(request))


@router.get("/ai-model-policies", response_model=list[AIModelPolicyRead])
def list_model_policies(organization_id: UUID, session: SessionDependency) -> list[AIModelPolicy]:
    return _list(session, AIModelPolicy, organization_id)


@router.get("/growthos-dashboard", response_model=GrowthDashboardRead)
def dashboard(organization_id: UUID, session: SessionDependency) -> GrowthDashboardRead:
    def count(model: type[ModelT], *criteria: Any) -> int:
        mapped = cast(Any, model)
        return int(
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(mapped.organization_id == organization_id, *criteria)
            )
            or 0
        )

    candidate_count = count(ProspectCandidate)
    qualified_candidates = count(ProspectCandidate, ProspectCandidate.status == "qualified")
    average_score = session.scalar(
        select(func.avg(ProspectQualificationAssessment.score)).where(
            ProspectQualificationAssessment.organization_id == organization_id,
            ProspectQualificationAssessment.score.is_not(None),
        )
    )
    top_results = list(
        session.scalars(
            select(GrowthBusinessResearchResult)
            .where(GrowthBusinessResearchResult.organization_id == organization_id)
            .order_by(GrowthBusinessResearchResult.confidence.desc())
            .limit(5)
        )
    )
    return GrowthDashboardRead(
        organization_id=organization_id,
        prospects_discovered=count(GrowthProspect) + candidate_count,
        qualified_prospects=(
            count(GrowthProspect, GrowthProspect.status == "qualified") + qualified_candidates
        ),
        opportunities_found=count(GrowthOpportunityAnalysis),
        gifts_created=count(GrowthGift),
        outreach_drafts=count(GrowthOutreachDraft),
        replies=count(GrowthProspect, GrowthProspect.status == "replied"),
        customers=count(GrowthProspect, GrowthProspect.status == "customer"),
        research_runs=count(GrowthBusinessResearchRun),
        top_opportunities=[
            {
                "research_result_id": str(item.id),
                "summary": item.summary,
                "confidence": item.confidence,
            }
            for item in top_results
        ],
        average_qualification_score=float(average_score) if average_score is not None else None,
        pending_human_review=(
            count(GrowthGift, GrowthGift.status == "review")
            + count(GrowthOutreachDraft, GrowthOutreachDraft.status == "human_review")
        ),
        active_revenue_experiments=count(RevenueExperiment, RevenueExperiment.status == "active"),
        prospects_awaiting_review=count(ProspectCandidate, ProspectCandidate.status == "qualified"),
        growth_gifts_ready=count(GrowthGift, GrowthGift.status == "ready_for_delivery"),
        outreach_waiting_approval=count(
            GrowthOutreachDraft, GrowthOutreachDraft.status == "human_review"
        ),
        replies_received=count(
            OutreachTrackingEvent,
            OutreachTrackingEvent.event_type == "reply_received",
        ),
        positive_conversations=count(
            SalesConversationAnalysis,
            SalesConversationAnalysis.buying_signal.in_(["positive", "strong"]),
        ),
        conversion_signals=count(
            OutreachTrackingEvent, OutreachTrackingEvent.event_type == "converted"
        ),
    )


@router.get("/growthos-revenue-v2-dashboard", response_model=GrowthRevenueV2Dashboard)
def revenue_v2_dashboard(
    organization_id: UUID, session: SessionDependency
) -> GrowthRevenueV2Dashboard:
    return GrowthRevenueService(session).v2_dashboard(organization_id)
