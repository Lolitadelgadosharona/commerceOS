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
    ProductCandidateRead,
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
def get_opportunity(opportunity_id: UUID, session: SessionDependency) -> MarketOpportunity:
    return _get_or_raise(session, MarketOpportunity, opportunity_id)


@router.patch(
    "/opportunities/{opportunity_id}",
    response_model=MarketOpportunityRead,
    tags=["opportunities"],
)
def update_opportunity(
    opportunity_id: UUID, payload: MarketOpportunityUpdate, session: SessionDependency
) -> MarketOpportunity:
    opportunity = _get_or_raise(session, MarketOpportunity, opportunity_id)
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
    payload: ProductCandidateCreate, session: SessionDependency
) -> ProductCandidate:
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
