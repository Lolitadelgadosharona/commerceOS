from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.research_models import (
    CustomerPainResearch,
    MarketInsightResearch,
    OpportunityResearchBrief,
    ResearchAnalysis,
    ResearchEvidenceCitation,
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
