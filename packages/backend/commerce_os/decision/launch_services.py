from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.launch_models import (
    LaunchPreparationPackage,
    OfferStrategy,
    ProductObjectionMap,
    ProductPositioning,
)
from commerce_os.decision.launch_schemas import (
    LaunchPackageCreate,
    OfferStrategyCreate,
    ProductObjectionCreate,
    ProductPositioningCreate,
)
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
READINESS_POINTS = {"missing": 0.0, "review": 10.0, "ready": 20.0}


class LaunchPreparationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_positioning(self, payload: ProductPositioningCreate) -> ProductPositioning:
        self._product(payload.product_id, payload.organization_id)
        return self._save(ProductPositioning(**payload.model_dump()))

    def create_offer(self, payload: OfferStrategyCreate) -> OfferStrategy:
        self._product(payload.product_id, payload.organization_id)
        return self._save(OfferStrategy(**payload.model_dump()))

    def create_objection(self, payload: ProductObjectionCreate) -> ProductObjectionMap:
        self._product(payload.product_id, payload.organization_id)
        return self._save(ProductObjectionMap(**payload.model_dump()))

    def prepare_package(self, payload: LaunchPackageCreate) -> LaunchPreparationPackage:
        self._product(payload.product_id, payload.organization_id)
        positioning = self._latest(ProductPositioning, payload.product_id, payload.organization_id)
        offer = self._latest(OfferStrategy, payload.product_id, payload.organization_id)
        objection_count = self.session.scalar(
            select(func.count())
            .select_from(ProductObjectionMap)
            .where(
                ProductObjectionMap.organization_id == payload.organization_id,
                ProductObjectionMap.product_id == payload.product_id,
            )
        )
        creative = self._source_status(
            "creative_strategies", payload.product_id, payload.organization_id
        )
        listing = self._source_status(
            "listing_strategies", payload.product_id, payload.organization_id
        )
        statuses = {
            "positioning_status": self._confidence_status(positioning),
            "offer_status": self._confidence_status(offer),
            "objection_status": "ready" if objection_count else "missing",
            "creative_readiness": self._strategy_status(creative),
            "listing_readiness": self._strategy_status(listing),
        }
        score = sum(READINESS_POINTS[status] for status in statuses.values())
        return self._save(
            LaunchPreparationPackage(
                **payload.model_dump(),
                **statuses,
                launch_score=score,
            )
        )

    def _product(self, product_id: UUID, organization_id: UUID) -> None:
        table = Base.metadata.tables["products"]
        status = self.session.scalar(
            select(table.c.status).where(
                table.c.id == product_id,
                table.c.organization_id == organization_id,
            )
        )
        if status is None:
            raise DecisionScopeError("Product was not found in this organization.")
        if status not in {"approved", "active"}:
            raise DecisionStateError(
                "Launch preparation requires an approved or active Build product."
            )

    def _latest(
        self, model: type[EntityT], product_id: UUID, organization_id: UUID
    ) -> EntityT | None:
        mapped = cast(Any, model)
        return self.session.scalar(
            select(model)
            .where(
                mapped.organization_id == organization_id,
                mapped.product_id == product_id,
            )
            .order_by(mapped.created_at.desc(), mapped.id.desc())
        )

    @staticmethod
    def _confidence_status(entity: ProductPositioning | OfferStrategy | None) -> str:
        if entity is None:
            return "missing"
        return "ready" if entity.confidence >= 0.7 else "review"

    @staticmethod
    def _strategy_status(status: str | None) -> str:
        if status is None:
            return "missing"
        return "ready" if status in {"approved", "active"} else "review"

    def _source_status(
        self, table_name: str, product_id: UUID, organization_id: UUID
    ) -> str | None:
        table = Base.metadata.tables[table_name]
        return cast(
            str | None,
            self.session.scalar(
                select(table.c.status).where(
                    table.c.product_id == product_id,
                    table.c.organization_id == organization_id,
                )
            ),
        )

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
