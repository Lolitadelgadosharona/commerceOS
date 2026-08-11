from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.build.creative_execution_schemas import JobStateUpdate
from commerce_os.build.creative_execution_services import CreativeExecutionService
from commerce_os.build.creative_generation_models import (
    CreativeGenerationJob,
    CreativeGenerationRequest,
    CreativeProviderCapability,
    CreativeQualityReview,
)
from commerce_os.build.creative_generation_schemas import (
    GenerationJobCreate,
    GenerationJobRead,
    GenerationRequestCreate,
    GenerationRequestRead,
    GenerationRequestUpdate,
    ProviderCapabilityCreate,
    ProviderCapabilityRead,
    QualityReviewCreate,
    QualityReviewRead,
)
from commerce_os.build.creative_generation_services import CreativeGenerationService
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


@router.post("/creative-generation-requests", response_model=GenerationRequestRead, status_code=201)
def create_request(
    payload: GenerationRequestCreate, session: SessionDependency
) -> CreativeGenerationRequest:
    return CreativeGenerationService(session).create_request(payload)


@router.get("/creative-generation-requests", response_model=list[GenerationRequestRead])
def list_requests(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeGenerationRequest]:
    return _list(session, CreativeGenerationRequest, organization_id)


@router.patch("/creative-generation-requests/{request_id}", response_model=GenerationRequestRead)
def update_request(
    request_id: UUID, payload: GenerationRequestUpdate, session: SessionDependency
) -> CreativeGenerationRequest:
    return CreativeGenerationService(session).transition_request(
        request_id, payload.organization_id, payload.status
    )


@router.post("/creative-providers", response_model=ProviderCapabilityRead, status_code=201)
def create_provider(
    payload: ProviderCapabilityCreate, session: SessionDependency
) -> CreativeProviderCapability:
    return CreativeGenerationService(session).create_provider(payload)


@router.get("/creative-providers", response_model=list[ProviderCapabilityRead])
def list_providers(
    organization_id: UUID, session: SessionDependency
) -> list[CreativeProviderCapability]:
    return _list(session, CreativeProviderCapability, organization_id)


@router.post("/creative-generation-jobs", response_model=GenerationJobRead, status_code=201)
def create_job(payload: GenerationJobCreate, session: SessionDependency) -> CreativeGenerationJob:
    return CreativeGenerationService(session).create_job(payload)


@router.get("/creative-generation-jobs", response_model=list[GenerationJobRead])
def list_jobs(organization_id: UUID, session: SessionDependency) -> list[CreativeGenerationJob]:
    return _list(session, CreativeGenerationJob, organization_id)


@router.patch("/creative-generation-jobs/{job_id}", response_model=GenerationJobRead)
def update_job(
    job_id: UUID, payload: JobStateUpdate, session: SessionDependency
) -> CreativeGenerationJob:
    return CreativeExecutionService(session).transition_job(
        job_id, payload.organization_id, payload.status, payload.failure_reason
    )


@router.post("/creative-quality-reviews", response_model=QualityReviewRead, status_code=201)
def create_review(
    payload: QualityReviewCreate, session: SessionDependency
) -> CreativeQualityReview:
    return CreativeGenerationService(session).create_review(payload)


@router.get("/creative-quality-reviews", response_model=list[QualityReviewRead])
def list_reviews(organization_id: UUID, session: SessionDependency) -> list[CreativeQualityReview]:
    return _list(session, CreativeQualityReview, organization_id)
