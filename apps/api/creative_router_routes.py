from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.decision.creative_router_models import (
    AssetStrategyStatus,
    CreativeAssetStrategy,
    CreativeEconomicAssessment,
    CreativeModelProvider,
    CreativePatternReference,
    CreativeRoutingDecision,
)
from commerce_os.decision.creative_router_schemas import (
    AssetStrategyCreate,
    AssetStrategyRead,
    AssetStrategyUpdate,
    EconomicAssessmentCreate,
    EconomicAssessmentRead,
    ModelProviderCreate,
    ModelProviderRead,
    PatternCreate,
    PatternRead,
    RoutingDecisionCreate,
    RoutingDecisionRead,
)
from commerce_os.decision.creative_router_services import (
    CreativeRouterService,
    scoped_asset_strategy,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


@router.post("/creative-asset-strategies", response_model=AssetStrategyRead, status_code=201)
def create_asset_strategy(
    payload: AssetStrategyCreate, session: SessionDependency
) -> CreativeAssetStrategy:
    return CreativeRouterService(session).create_asset_strategy(payload)


@router.get("/creative-asset-strategies", response_model=list[AssetStrategyRead])
def list_asset_strategies(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeAssetStrategy]:
    return _list(session, CreativeAssetStrategy, organization_id)


@router.patch("/creative-asset-strategies/{strategy_id}", response_model=AssetStrategyRead)
def transition_asset_strategy(
    strategy_id: UUID,
    organization_id: UUID,
    payload: AssetStrategyUpdate,
    session: SessionDependency,
) -> CreativeAssetStrategy:
    return CreativeRouterService(session).transition_asset_strategy(
        scoped_asset_strategy(session, strategy_id, organization_id),
        AssetStrategyStatus(payload.status),
    )


@router.post("/creative-model-providers", response_model=ModelProviderRead, status_code=201)
def create_provider(
    payload: ModelProviderCreate, session: SessionDependency
) -> CreativeModelProvider:
    return CreativeRouterService(session).create_provider(payload)


@router.get("/creative-model-providers", response_model=list[ModelProviderRead])
def list_providers(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeModelProvider]:
    return _list(session, CreativeModelProvider, organization_id)


@router.post("/creative-routing-decisions", response_model=RoutingDecisionRead, status_code=201)
def create_routing_decision(
    payload: RoutingDecisionCreate, session: SessionDependency
) -> CreativeRoutingDecision:
    return CreativeRouterService(session).route(payload)


@router.get("/creative-routing-decisions", response_model=list[RoutingDecisionRead])
def list_routing_decisions(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeRoutingDecision]:
    return _list(session, CreativeRoutingDecision, organization_id)


@router.post(
    "/creative-economic-assessments", response_model=EconomicAssessmentRead, status_code=201
)
def create_economic_assessment(
    payload: EconomicAssessmentCreate, session: SessionDependency
) -> CreativeEconomicAssessment:
    return CreativeRouterService(session).assess_economics(payload)


@router.get("/creative-economic-assessments", response_model=list[EconomicAssessmentRead])
def list_economic_assessments(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeEconomicAssessment]:
    return _list(session, CreativeEconomicAssessment, organization_id)


@router.post("/creative-patterns", response_model=PatternRead, status_code=201)
def create_pattern(payload: PatternCreate, session: SessionDependency) -> CreativePatternReference:
    return CreativeRouterService(session).create_pattern(payload)


@router.get("/creative-patterns", response_model=list[PatternRead])
def list_patterns(
    organization_id: UUID, session: SessionDependency
) -> list[CreativePatternReference]:
    return _list(session, CreativePatternReference, organization_id)
