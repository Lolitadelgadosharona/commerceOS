from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.launch_models import (
    LaunchPreparationPackage,
    OfferStrategy,
    ProductObjectionMap,
    ProductPositioning,
)
from commerce_os.decision.launch_schemas import (
    LaunchPackageCreate,
    LaunchPackageRead,
    OfferStrategyCreate,
    OfferStrategyRead,
    ProductObjectionCreate,
    ProductObjectionRead,
    ProductPositioningCreate,
    ProductPositioningRead,
)
from commerce_os.decision.launch_services import LaunchPreparationService
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


@router.post("/product-positioning", response_model=ProductPositioningRead, status_code=201)
def create_positioning(
    payload: ProductPositioningCreate, session: SessionDependency
) -> ProductPositioning:
    return LaunchPreparationService(session).create_positioning(payload)


@router.get("/product-positioning", response_model=list[ProductPositioningRead])
def list_positioning(organization_id: UUID, session: SessionDependency) -> list[ProductPositioning]:
    return _list(session, ProductPositioning, organization_id)


@router.post("/offer-strategies", response_model=OfferStrategyRead, status_code=201)
def create_offer(payload: OfferStrategyCreate, session: SessionDependency) -> OfferStrategy:
    return LaunchPreparationService(session).create_offer(payload)


@router.get("/offer-strategies", response_model=list[OfferStrategyRead])
def list_offers(organization_id: UUID, session: SessionDependency) -> list[OfferStrategy]:
    return _list(session, OfferStrategy, organization_id)


@router.post("/product-objections", response_model=ProductObjectionRead, status_code=201)
def create_objection(
    payload: ProductObjectionCreate, session: SessionDependency
) -> ProductObjectionMap:
    return LaunchPreparationService(session).create_objection(payload)


@router.get("/product-objections", response_model=list[ProductObjectionRead])
def list_objections(organization_id: UUID, session: SessionDependency) -> list[ProductObjectionMap]:
    return _list(session, ProductObjectionMap, organization_id)


@router.post("/launch-packages", response_model=LaunchPackageRead, status_code=201)
def create_package(
    payload: LaunchPackageCreate, session: SessionDependency
) -> LaunchPreparationPackage:
    return LaunchPreparationService(session).prepare_package(payload)


@router.get("/launch-packages", response_model=list[LaunchPackageRead])
def list_packages(
    organization_id: UUID, session: SessionDependency
) -> list[LaunchPreparationPackage]:
    return _list(session, LaunchPreparationPackage, organization_id)
