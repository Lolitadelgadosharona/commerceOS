from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.build.creative_asset_models import (
    CreativeAsset,
    CreativeAssetVersion,
    CreativePerformanceObservation,
)
from commerce_os.build.creative_asset_schemas import (
    CreativeAssetCreate,
    CreativeAssetVersionCreate,
    CreativePerformanceCreate,
)
from commerce_os.build.errors import BuildScopeError, BuildStateError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)


class CreativeAssetService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_asset(self, payload: CreativeAssetCreate) -> CreativeAsset:
        if not reference_belongs_to_organization(
            self.session,
            table_name="products",
            reference_id=payload.product_id,
            organization_id=payload.organization_id,
        ):
            raise BuildScopeError("Product was not found in this organization.")
        values = payload.model_dump(exclude={"metadata"})
        return self._save(CreativeAsset(**values, asset_metadata=payload.metadata))

    def create_version(self, payload: CreativeAssetVersionCreate) -> CreativeAssetVersion:
        asset = self._asset(payload.asset_id, payload.organization_id)
        current = self.session.scalar(
            select(func.max(CreativeAssetVersion.version_number)).where(
                CreativeAssetVersion.asset_id == asset.id
            )
        )
        next_version = (current or 0) + 1
        return self._save(
            CreativeAssetVersion(
                **payload.model_dump(),
                version_number=next_version,
            )
        )

    def create_observation(
        self, payload: CreativePerformanceCreate
    ) -> CreativePerformanceObservation:
        self._asset(payload.asset_id, payload.organization_id)
        return self._save(
            CreativePerformanceObservation(
                **payload.model_dump(exclude={"metric_value"}),
                metric_value=payload.metric_value.quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_UP
                ),
            )
        )

    def _asset(self, asset_id: UUID, organization_id: UUID) -> CreativeAsset:
        asset = self.session.get(CreativeAsset, asset_id)
        if asset is None or asset.organization_id != organization_id:
            raise BuildScopeError("Creative asset was not found in this organization.")
        if asset.approval_status not in {"pending", "approved", "rejected"}:
            raise BuildStateError("Creative asset approval state is invalid.")
        return asset

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
