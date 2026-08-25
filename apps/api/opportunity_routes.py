from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.intelligence.discovery_models import OpportunityCandidate
from commerce_os.intelligence.discovery_schemas import (
    OpportunityCandidateCreate,
    OpportunityCandidateRead,
)
from commerce_os.intelligence.discovery_services import OpportunityDiscoveryService
from commerce_os.intelligence.errors import IntelligenceNotFoundError
from commerce_os.intelligence.opportunity_models import (
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    OpportunityStatus,
    ProductCandidate,
    ProductCandidateEvidence,
    ProductEvaluation,
)
from commerce_os.intelligence.opportunity_schemas import (
    MarketOpportunityCreate,
    MarketOpportunityRead,
    MarketOpportunityUpdate,
    OpportunityEvidenceCreate,
    OpportunityEvidenceRead,
    OpportunityRiskCreate,
    OpportunityRiskRead,
    OpportunityScoreCreate,
    OpportunityScoreRead,
    ProductCandidateCreate,
    ProductCandidateEvidenceRead,
    ProductCandidateRead,
    ProductCandidateReview,
    ProductEvaluationDashboard,
    ProductEvaluationRead,
    ProductOpportunityCandidateCreate,
)
from commerce_os.intelligence.opportunity_services import (
    OpportunityRiskService,
    OpportunityScoringService,
    OpportunityService,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _get_or_raise(session: Session, model: type[ModelT], entity_id: UUID) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise IntelligenceNotFoundError("The requested opportunity resource was not found.")
    return entity


def _get_scoped_market_opportunity(
    session: Session, opportunity_id: UUID, organization_id: UUID
) -> MarketOpportunity:
    opportunity = session.scalar(
        select(MarketOpportunity).where(
            MarketOpportunity.id == opportunity_id,
            MarketOpportunity.organization_id == organization_id,
        )
    )
    if opportunity is None:
        raise IntelligenceNotFoundError(
            "The requested opportunity was not found in this organization."
        )
    return opportunity


def _list_for_organization(
    session: Session, model: type[ModelT], organization_id: UUID
) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post(
    "/opportunities",
    response_model=MarketOpportunityRead | OpportunityCandidateRead,
    status_code=201,
    tags=["opportunities"],
)
def create_opportunity(
    payload: MarketOpportunityCreate | OpportunityCandidateCreate,
    request: Request,
    session: SessionDependency,
) -> MarketOpportunity | OpportunityCandidate:
    if isinstance(payload, OpportunityCandidateCreate):
        from apps.api.opportunity_discovery_routes import actor_id

        return OpportunityDiscoveryService(session).create_candidate(payload, actor_id(request))
    opportunity = MarketOpportunity(**payload.model_dump())
    session.add(opportunity)
    session.commit()
    session.refresh(opportunity)
    return opportunity


@router.get(
    "/opportunities",
    response_model=list[MarketOpportunityRead | OpportunityCandidateRead],
    tags=["opportunities"],
)
def list_opportunities(
    organization_id: UUID, session: SessionDependency
) -> list[MarketOpportunity | OpportunityCandidate]:
    markets = _list_for_organization(session, MarketOpportunity, organization_id)
    candidates = _list_for_organization(session, OpportunityCandidate, organization_id)
    return [*candidates, *markets]


@router.get(
    "/opportunities/{opportunity_id}",
    response_model=MarketOpportunityRead,
    tags=["opportunities"],
)
def get_opportunity(
    opportunity_id: UUID, organization_id: UUID, session: SessionDependency
) -> MarketOpportunity:
    return _get_scoped_market_opportunity(session, opportunity_id, organization_id)


@router.patch(
    "/opportunities/{opportunity_id}",
    response_model=MarketOpportunityRead,
    tags=["opportunities"],
)
def update_opportunity(
    opportunity_id: UUID,
    organization_id: UUID,
    payload: MarketOpportunityUpdate,
    session: SessionDependency,
) -> MarketOpportunity:
    opportunity = _get_scoped_market_opportunity(session, opportunity_id, organization_id)
    opportunity.status = OpportunityStatus(payload.status)
    session.commit()
    session.refresh(opportunity)
    return opportunity


@router.post(
    "/opportunity-evidence",
    response_model=OpportunityEvidenceRead,
    status_code=201,
    tags=["opportunity_evidence"],
)
def create_opportunity_evidence(
    payload: OpportunityEvidenceCreate, session: SessionDependency
) -> OpportunityEvidence:
    return OpportunityService(session).add_evidence(payload)


@router.get(
    "/opportunity-evidence",
    response_model=list[OpportunityEvidenceRead],
    tags=["opportunity_evidence"],
)
def list_opportunity_evidence(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityEvidence]:
    return _list_for_organization(session, OpportunityEvidence, organization_id)


@router.get(
    "/opportunity-evidence/{evidence_id}",
    response_model=OpportunityEvidenceRead,
    tags=["opportunity_evidence"],
)
def get_opportunity_evidence(evidence_id: UUID, session: SessionDependency) -> OpportunityEvidence:
    return _get_or_raise(session, OpportunityEvidence, evidence_id)


@router.post(
    "/product-candidates",
    response_model=ProductCandidateRead,
    status_code=201,
    tags=["product_candidates"],
)
def create_product_candidate(
    payload: ProductCandidateCreate | ProductOpportunityCandidateCreate,
    request: Request,
    session: SessionDependency,
) -> ProductCandidate:
    if isinstance(payload, ProductOpportunityCandidateCreate):
        from apps.api.opportunity_discovery_routes import actor_id

        return OpportunityService(session).evaluate_candidate(payload, actor_id(request))
    return OpportunityService(session).add_candidate(payload)


@router.get(
    "/product-candidates",
    response_model=list[ProductCandidateRead],
    tags=["product_candidates"],
)
def list_product_candidates(
    organization_id: UUID, session: SessionDependency
) -> list[ProductCandidate]:
    return _list_for_organization(session, ProductCandidate, organization_id)


@router.get(
    "/product-candidates/{candidate_id}",
    response_model=ProductCandidateRead,
    tags=["product_candidates"],
)
def get_product_candidate(candidate_id: UUID, session: SessionDependency) -> ProductCandidate:
    return _get_or_raise(session, ProductCandidate, candidate_id)


@router.get(
    "/product-candidates/{candidate_id}/evaluation",
    response_model=ProductEvaluationRead,
    tags=["product_candidates"],
)
def get_product_evaluation(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> ProductEvaluation:
    return OpportunityService(session).evaluation(candidate_id, organization_id)


@router.get(
    "/product-candidates/{candidate_id}/evidence",
    response_model=list[ProductCandidateEvidenceRead],
    tags=["product_candidates"],
)
def get_product_candidate_evidence(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> list[ProductCandidateEvidence]:
    return OpportunityService(session).evidence(candidate_id, organization_id)


@router.post(
    "/product-candidates/{candidate_id}/review",
    response_model=ProductCandidateRead,
    tags=["product_candidates"],
)
def review_product_candidate(
    candidate_id: UUID,
    organization_id: UUID,
    payload: ProductCandidateReview,
    request: Request,
    session: SessionDependency,
) -> ProductCandidate:
    from apps.api.opportunity_discovery_routes import actor_id

    service = OpportunityService(session)
    candidate = service._candidate(candidate_id, organization_id)
    return service.review(candidate, payload.action, payload.approval_request_id, actor_id(request))


@router.get(
    "/product-evaluation-dashboard",
    response_model=ProductEvaluationDashboard,
    tags=["product_candidates"],
)
def product_evaluation_dashboard(
    organization_id: UUID, session: SessionDependency
) -> ProductEvaluationDashboard:
    return OpportunityService(session).dashboard(organization_id)


@router.post(
    "/opportunity-scores",
    response_model=OpportunityScoreRead,
    tags=["opportunity_scores"],
)
def score_opportunity(
    payload: OpportunityScoreCreate, session: SessionDependency
) -> OpportunityScore:
    return OpportunityScoringService(session).score(payload)


@router.get(
    "/opportunity-scores",
    response_model=list[OpportunityScoreRead],
    tags=["opportunity_scores"],
)
def list_opportunity_scores(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityScore]:
    return _list_for_organization(session, OpportunityScore, organization_id)


@router.get(
    "/opportunity-scores/{score_id}",
    response_model=OpportunityScoreRead,
    tags=["opportunity_scores"],
)
def get_opportunity_score(score_id: UUID, session: SessionDependency) -> OpportunityScore:
    return _get_or_raise(session, OpportunityScore, score_id)


@router.post(
    "/opportunity-risks",
    response_model=OpportunityRiskRead,
    status_code=201,
    tags=["opportunity_risks"],
)
def create_opportunity_risk(
    payload: OpportunityRiskCreate, session: SessionDependency
) -> OpportunityRisk:
    return OpportunityRiskService(session).create(payload)


@router.get(
    "/opportunity-risks",
    response_model=list[OpportunityRiskRead],
    tags=["opportunity_risks"],
)
def list_opportunity_risks(
    organization_id: UUID, session: SessionDependency
) -> list[OpportunityRisk]:
    return _list_for_organization(session, OpportunityRisk, organization_id)


@router.get(
    "/opportunity-risks/{risk_id}",
    response_model=OpportunityRiskRead,
    tags=["opportunity_risks"],
)
def get_opportunity_risk(risk_id: UUID, session: SessionDependency) -> OpportunityRisk:
    return _get_or_raise(session, OpportunityRisk, risk_id)
