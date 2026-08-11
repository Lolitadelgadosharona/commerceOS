from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.build.creative_asset_models import (
    CreativeAsset,
    CreativeAssetVersion,
    CreativePerformanceObservation,
)
from commerce_os.build.creative_asset_schemas import (
    CreativeAssetCreate,
    CreativeAssetRead,
    CreativeAssetVersionCreate,
    CreativeAssetVersionRead,
    CreativePerformanceCreate,
    CreativePerformanceRead,
)
from commerce_os.build.creative_asset_services import CreativeAssetService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/creative-assets", response_model=CreativeAssetRead, status_code=201)
def create_asset(payload: CreativeAssetCreate, session: SessionDependency) -> CreativeAsset:
    return CreativeAssetService(session).create_asset(payload)


@router.get("/creative-assets", response_model=list[CreativeAssetRead])
def list_assets(organization_id: UUID, session: SessionDependency) -> list[CreativeAsset]:
    return _list(session, CreativeAsset, organization_id)


@router.post("/creative-versions", response_model=CreativeAssetVersionRead, status_code=201)
def create_version(
    payload: CreativeAssetVersionCreate, session: SessionDependency
) -> CreativeAssetVersion:
    return CreativeAssetService(session).create_version(payload)


@router.get("/creative-versions", response_model=list[CreativeAssetVersionRead])
def list_versions(organization_id: UUID, session: SessionDependency) -> list[CreativeAssetVersion]:
    return _list(session, CreativeAssetVersion, organization_id)


@router.post("/creative-performance", response_model=CreativePerformanceRead, status_code=201)
def create_performance(
    payload: CreativePerformanceCreate, session: SessionDependency
) -> CreativePerformanceObservation:
    return CreativeAssetService(session).create_observation(payload)


@router.get("/creative-performance", response_model=list[CreativePerformanceRead])
def list_performance(
    organization_id: UUID, session: SessionDependency
) -> list[CreativePerformanceObservation]:
    return _list(session, CreativePerformanceObservation, organization_id)
