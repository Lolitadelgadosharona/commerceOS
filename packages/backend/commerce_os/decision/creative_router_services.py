from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.decision.creative_models import CreativeStrategy
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
    EconomicAssessmentCreate,
    ModelProviderCreate,
    PatternCreate,
    RoutingDecisionCreate,
)
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
STRATEGY_TRANSITIONS = {
    "draft": {"recommended", "archived"},
    "recommended": {"approved", "archived"},
    "approved": {"archived"},
    "archived": set(),
}
ROUTING_WEIGHTS = {
    "quality": 0.30,
    "cost": 0.20,
    "speed": 0.15,
    "platform_suitability": 0.20,
    "historical_performance": 0.15,
}


def scoped_asset_strategy(
    session: Session, entity_id: UUID, organization_id: UUID
) -> CreativeAssetStrategy:
    entity = session.get(CreativeAssetStrategy, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise DecisionScopeError("Creative asset strategy was not found in this organization.")
    return entity


class CreativeRouterService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_asset_strategy(self, payload: AssetStrategyCreate) -> CreativeAssetStrategy:
        if not reference_belongs_to_organization(
            self.session,
            table_name="products",
            reference_id=payload.product_id,
            organization_id=payload.organization_id,
        ):
            raise DecisionScopeError("Product was not found in this organization.")
        strategy = self.session.get(CreativeStrategy, payload.creative_strategy_id)
        if (
            strategy is None
            or strategy.organization_id != payload.organization_id
            or strategy.product_id != payload.product_id
        ):
            raise DecisionScopeError(
                "Creative strategy does not match the product and organization."
            )
        return self._save(
            CreativeAssetStrategy(**payload.model_dump(), status=AssetStrategyStatus.DRAFT)
        )

    def transition_asset_strategy(
        self, strategy: CreativeAssetStrategy, status: AssetStrategyStatus
    ) -> CreativeAssetStrategy:
        if status.value not in STRATEGY_TRANSITIONS[str(strategy.status)]:
            raise DecisionStateError(
                f"Asset strategy cannot transition from {strategy.status} to {status.value}."
            )
        strategy.status = status
        return self._save(strategy)

    def create_provider(self, payload: ModelProviderCreate) -> CreativeModelProvider:
        if not self._organization_exists(payload.organization_id):
            raise DecisionScopeError("Organization was not found.")
        return self._save(CreativeModelProvider(**payload.model_dump()))

    def route(self, payload: RoutingDecisionCreate) -> CreativeRoutingDecision:
        scoped_asset_strategy(self.session, payload.asset_strategy_id, payload.organization_id)
        for score_map in (payload.platform_suitability, payload.historical_performance):
            if any(value < 0 or value > 100 for value in score_map.values()):
                raise DecisionStateError("Routing factor scores must be between 0 and 100.")
        candidates: list[tuple[float, CreativeModelProvider, dict[str, float | None]]] = []
        for provider_id in set(payload.candidate_provider_ids):
            provider = self.session.get(CreativeModelProvider, provider_id)
            if (
                provider is None
                or provider.organization_id != payload.organization_id
                or provider.capability_type != payload.capability_required
                or not provider.availability
                or provider.status != "active"
            ):
                continue
            factors: dict[str, float | None] = {
                "quality": provider.quality_score,
                "cost": provider.cost_score,
                "speed": provider.speed_score,
                "platform_suitability": payload.platform_suitability.get(provider.id),
                "historical_performance": payload.historical_performance.get(provider.id),
            }
            present_weight = sum(
                ROUTING_WEIGHTS[name] for name, value in factors.items() if value is not None
            )
            score = (
                sum(
                    float(value) * ROUTING_WEIGHTS[name]
                    for name, value in factors.items()
                    if value is not None
                )
                / present_weight
            )
            candidates.append((round(score, 2), provider, factors))
        if not candidates:
            raise DecisionStateError(
                "No active, available provider matches the required capability."
            )
        routing_score, provider, factors = max(
            candidates, key=lambda item: (item[0], str(item[1].id))
        )
        return self._save(
            CreativeRoutingDecision(
                organization_id=payload.organization_id,
                asset_strategy_id=payload.asset_strategy_id,
                capability_required=payload.capability_required,
                selected_provider_id=provider.id,
                reason=payload.reason,
                confidence=payload.confidence,
                factor_snapshot=factors,
                routing_score=routing_score,
                router_version="creative-router-v1.0",
            )
        )

    def assess_economics(self, payload: EconomicAssessmentCreate) -> CreativeEconomicAssessment:
        strategy = self.session.get(CreativeStrategy, payload.creative_strategy_id)
        if strategy is None or strategy.organization_id != payload.organization_id:
            raise DecisionScopeError("Creative strategy was not found in this organization.")
        risk_adjusted_value = payload.expected_impact * payload.confidence + payload.test_value
        denominator = max(
            payload.estimated_production_cost + payload.expected_impact + payload.test_value, 1
        )
        score = round(
            max(
                0,
                min(
                    100,
                    50
                    + 50 * (risk_adjusted_value - payload.estimated_production_cost) / denominator,
                ),
            ),
            2,
        )
        return self._save(
            CreativeEconomicAssessment(
                **payload.model_dump(),
                profitability_score=score,
                formula_version="creative-economics-v1.0",
            )
        )

    def create_pattern(self, payload: PatternCreate) -> CreativePatternReference:
        if not self._organization_exists(payload.organization_id):
            raise DecisionScopeError("Organization was not found.")
        return self._save(CreativePatternReference(**payload.model_dump()))

    def _organization_exists(self, organization_id: UUID) -> bool:
        table = Base.metadata.tables["organizations"]
        return (
            self.session.execute(
                select(table.c.id).where(table.c.id == organization_id)
            ).scalar_one_or_none()
            is not None
        )

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
