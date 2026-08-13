from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.governance.models import User
from commerce_os.intelligence.connector_models import (
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
    NormalizedMarketItem,
)
from commerce_os.intelligence.connector_schemas import (
    ConnectorCreate,
    ConnectorRead,
    ConnectorUpdate,
    IngestionJobCreate,
    IngestionJobRead,
    IngestionJobUpdate,
    MarketDataRecordCreate,
    MarketDataRecordRead,
    NormalizedMarketItemCreate,
    NormalizedMarketItemRead,
)
from commerce_os.intelligence.connector_services import MarketConnectorService, scoped_connector
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def initiating_actor(request: Request) -> UUID | None:
    actor = getattr(request.state, "actor", None)
    if isinstance(actor, User):
        return actor.id
    if getattr(request.app.state, "auth_test_bypass", False):
        raw = request.headers.get("X-Actor-ID")
        return UUID(raw) if raw else None
    return None


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped_model = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped_model.organization_id == organization_id)
            .order_by(mapped_model.created_at.desc())
        )
    )


@router.post("/connectors", response_model=ConnectorRead, status_code=201)
def create_connector(
    payload: ConnectorCreate, request: Request, session: SessionDependency
) -> MarketConnectorDefinition:
    return MarketConnectorService(session).create_connector(payload, initiating_actor(request))


@router.get("/connectors", response_model=list[ConnectorRead])
def list_connectors(
    organization_id: UUID, session: SessionDependency
) -> list[MarketConnectorDefinition]:
    return _list(session, MarketConnectorDefinition, organization_id)


@router.patch("/connectors/{connector_id}", response_model=ConnectorRead)
def transition_connector(
    connector_id: UUID,
    organization_id: UUID,
    payload: ConnectorUpdate,
    request: Request,
    session: SessionDependency,
) -> MarketConnectorDefinition:
    connector = scoped_connector(session, MarketConnectorDefinition, connector_id, organization_id)
    return MarketConnectorService(session).transition_connector(
        connector, payload.status, initiating_actor(request)
    )


@router.post("/market-data-records", response_model=MarketDataRecordRead, status_code=201)
def create_record(
    payload: MarketDataRecordCreate, request: Request, session: SessionDependency
) -> MarketDataRecord:
    return MarketConnectorService(session).store_record(payload, initiating_actor(request))


@router.get("/market-data-records", response_model=list[MarketDataRecordRead])
def list_records(organization_id: UUID, session: SessionDependency) -> list[MarketDataRecord]:
    return _list(session, MarketDataRecord, organization_id)


@router.post("/normalized-market-items", response_model=NormalizedMarketItemRead, status_code=201)
def create_normalized_item(
    payload: NormalizedMarketItemCreate, request: Request, session: SessionDependency
) -> NormalizedMarketItem:
    return MarketConnectorService(session).normalize(payload, initiating_actor(request))


@router.get("/normalized-market-items", response_model=list[NormalizedMarketItemRead])
def list_normalized_items(
    organization_id: UUID, session: SessionDependency
) -> list[NormalizedMarketItem]:
    return _list(session, NormalizedMarketItem, organization_id)


@router.post("/ingestion-jobs", response_model=IngestionJobRead, status_code=201)
def create_ingestion_job(
    payload: IngestionJobCreate, request: Request, session: SessionDependency
) -> MarketIngestionJob:
    return MarketConnectorService(session).create_job(payload, initiating_actor(request))


@router.get("/ingestion-jobs", response_model=list[IngestionJobRead])
def list_ingestion_jobs(
    organization_id: UUID, session: SessionDependency
) -> list[MarketIngestionJob]:
    return _list(session, MarketIngestionJob, organization_id)


@router.patch("/ingestion-jobs/{job_id}", response_model=IngestionJobRead)
def transition_ingestion_job(
    job_id: UUID,
    organization_id: UUID,
    payload: IngestionJobUpdate,
    request: Request,
    session: SessionDependency,
) -> MarketIngestionJob:
    job = scoped_connector(session, MarketIngestionJob, job_id, organization_id)
    return MarketConnectorService(session).transition_job(job, payload, initiating_actor(request))
