from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.intelligence.errors import IntelligenceNotFoundError
from commerce_os.intelligence.product_models import (
    ProductEconomics,
    ProductHypothesis,
    ProductInvestmentScore,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.intelligence.product_schemas import (
    ProductEconomicsCreate,
    ProductEconomicsRead,
    ProductHypothesisCreate,
    ProductHypothesisRead,
    ProductInvestmentScoreCreate,
    ProductInvestmentScoreRead,
    ProductRiskCreate,
    ProductRiskRead,
    SupplierCandidateCreate,
    SupplierCandidateRead,
)
from commerce_os.intelligence.product_services import (
    ProductEconomicsService,
    ProductHypothesisService,
    ProductInvestmentScoringService,
    ProductRiskService,
    SupplierCandidateService,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _get(session: Session, model: type[ModelT], entity_id: UUID) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise IntelligenceNotFoundError(
            "The requested product intelligence resource was not found."
        )
    return entity


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post(
    "/product-hypotheses",
    response_model=ProductHypothesisRead,
    status_code=201,
    tags=["product_hypotheses"],
)
def create_product_hypothesis(
    payload: ProductHypothesisCreate, session: SessionDependency
) -> ProductHypothesis:
    return ProductHypothesisService(session).create(payload)


@router.get(
    "/product-hypotheses", response_model=list[ProductHypothesisRead], tags=["product_hypotheses"]
)
def list_product_hypotheses(
    organization_id: UUID, session: SessionDependency
) -> list[ProductHypothesis]:
    return _list(session, ProductHypothesis, organization_id)


@router.get(
    "/product-hypotheses/{entity_id}",
    response_model=ProductHypothesisRead,
    tags=["product_hypotheses"],
)
def get_product_hypothesis(entity_id: UUID, session: SessionDependency) -> ProductHypothesis:
    return _get(session, ProductHypothesis, entity_id)


@router.post("/product-economics", response_model=ProductEconomicsRead, tags=["product_economics"])
def set_product_economics(
    payload: ProductEconomicsCreate, session: SessionDependency
) -> ProductEconomics:
    return ProductEconomicsService(session).upsert(payload)


@router.get(
    "/product-economics", response_model=list[ProductEconomicsRead], tags=["product_economics"]
)
def list_product_economics(
    organization_id: UUID, session: SessionDependency
) -> list[ProductEconomics]:
    return _list(session, ProductEconomics, organization_id)


@router.get(
    "/product-economics/{entity_id}",
    response_model=ProductEconomicsRead,
    tags=["product_economics"],
)
def get_product_economics(entity_id: UUID, session: SessionDependency) -> ProductEconomics:
    return _get(session, ProductEconomics, entity_id)


@router.post(
    "/supplier-candidates",
    response_model=SupplierCandidateRead,
    status_code=201,
    tags=["supplier_candidates"],
)
def create_supplier_candidate(
    payload: SupplierCandidateCreate, session: SessionDependency
) -> SupplierCandidate:
    return SupplierCandidateService(session).create(payload)


@router.get(
    "/supplier-candidates", response_model=list[SupplierCandidateRead], tags=["supplier_candidates"]
)
def list_supplier_candidates(
    organization_id: UUID, session: SessionDependency
) -> list[SupplierCandidate]:
    return _list(session, SupplierCandidate, organization_id)


@router.get(
    "/supplier-candidates/{entity_id}",
    response_model=SupplierCandidateRead,
    tags=["supplier_candidates"],
)
def get_supplier_candidate(entity_id: UUID, session: SessionDependency) -> SupplierCandidate:
    return _get(session, SupplierCandidate, entity_id)


@router.post(
    "/product-risks", response_model=ProductRiskRead, status_code=201, tags=["product_risks"]
)
def create_product_risk(payload: ProductRiskCreate, session: SessionDependency) -> ProductRisk:
    return ProductRiskService(session).create(payload)


@router.get("/product-risks", response_model=list[ProductRiskRead], tags=["product_risks"])
def list_product_risks(organization_id: UUID, session: SessionDependency) -> list[ProductRisk]:
    return _list(session, ProductRisk, organization_id)


@router.get("/product-risks/{entity_id}", response_model=ProductRiskRead, tags=["product_risks"])
def get_product_risk(entity_id: UUID, session: SessionDependency) -> ProductRisk:
    return _get(session, ProductRisk, entity_id)


@router.post(
    "/product-investment-scores",
    response_model=ProductInvestmentScoreRead,
    tags=["product_investment_scores"],
)
def score_product(
    payload: ProductInvestmentScoreCreate, session: SessionDependency
) -> ProductInvestmentScore:
    return ProductInvestmentScoringService(session).score(payload)


@router.get(
    "/product-investment-scores",
    response_model=list[ProductInvestmentScoreRead],
    tags=["product_investment_scores"],
)
def list_product_scores(
    organization_id: UUID, session: SessionDependency
) -> list[ProductInvestmentScore]:
    return _list(session, ProductInvestmentScore, organization_id)


@router.get(
    "/product-investment-scores/{entity_id}",
    response_model=ProductInvestmentScoreRead,
    tags=["product_investment_scores"],
)
def get_product_score(entity_id: UUID, session: SessionDependency) -> ProductInvestmentScore:
    return _get(session, ProductInvestmentScore, entity_id)
