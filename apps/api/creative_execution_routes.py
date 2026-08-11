from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.build.creative_execution_models import (
    CreativeArtifact,
    CreativeExecutionRecord,
    CreativeGenerationCostObservation,
)
from commerce_os.build.creative_execution_schemas import (
    CreativeArtifactCreate,
    CreativeArtifactRead,
    ExecutionRecordCreate,
    ExecutionRecordRead,
    GenerationCostCreate,
    GenerationCostRead,
)
from commerce_os.build.creative_execution_services import CreativeExecutionService
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


@router.post("/creative-execution-records", response_model=ExecutionRecordRead, status_code=201)
def create_record(
    payload: ExecutionRecordCreate, session: SessionDependency
) -> CreativeExecutionRecord:
    return CreativeExecutionService(session).create_record(payload)


@router.get("/creative-execution-records", response_model=list[ExecutionRecordRead])
def list_records(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeExecutionRecord]:
    return _list(session, CreativeExecutionRecord, organization_id)


@router.post("/creative-artifacts", response_model=CreativeArtifactRead, status_code=201)
def create_artifact(
    payload: CreativeArtifactCreate, session: SessionDependency
) -> CreativeArtifact:
    return CreativeExecutionService(session).create_artifact(payload)


@router.get("/creative-artifacts", response_model=list[CreativeArtifactRead])
def list_artifacts(organization_id: UUID, session: SessionDependency) -> list[CreativeArtifact]:
    return _list(session, CreativeArtifact, organization_id)


@router.post("/creative-generation-costs", response_model=GenerationCostRead, status_code=201)
def create_cost(
    payload: GenerationCostCreate, session: SessionDependency
) -> CreativeGenerationCostObservation:
    return CreativeExecutionService(session).create_cost(payload)


@router.get("/creative-generation-costs", response_model=list[GenerationCostRead])
def list_costs(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeGenerationCostObservation]:
    return _list(session, CreativeGenerationCostObservation, organization_id)
