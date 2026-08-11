from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    PainEvidence,
    RedditConnector,
)
from commerce_os.intelligence.reddit_client import RedditApiClient, RedditReadTransport
from commerce_os.intelligence.reddit_schemas import (
    PainCandidateCreate,
    PainCandidateRead,
    PainCandidateUpdate,
    PainEvidenceCreate,
    PainEvidenceRead,
    RedditConnectorCreate,
    RedditConnectorRead,
    RedditConnectorUpdate,
    RedditIngestionRead,
    RedditIngestionRequest,
)
from commerce_os.intelligence.reddit_services import RedditIntelligenceService, scoped_reddit
from commerce_os.shared.config import get_settings
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def get_reddit_transport() -> RedditReadTransport:
    settings = get_settings()
    client_id = settings.reddit_client_id
    client_secret = settings.reddit_client_secret
    user_agent = settings.reddit_user_agent
    if not client_id or not client_secret or not user_agent:
        from commerce_os.intelligence.errors import IntelligenceValidationError

        raise IntelligenceValidationError("Reddit OAuth configuration is not available.")
    return RedditApiClient(
        client_id,
        client_secret,
        user_agent,
    )


RedditTransportDependency = Annotated[RedditReadTransport, Depends(get_reddit_transport)]


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/reddit-connectors", response_model=RedditConnectorRead, status_code=201)
def create_reddit_connector(
    payload: RedditConnectorCreate, session: SessionDependency
) -> RedditConnector:
    return RedditIntelligenceService(session).create_connector(payload)


@router.get("/reddit-connectors", response_model=list[RedditConnectorRead])
def list_reddit_connectors(
    organization_id: UUID, session: SessionDependency
) -> list[RedditConnector]:
    return _list(session, RedditConnector, organization_id)


@router.patch("/reddit-connectors/{connector_id}", response_model=RedditConnectorRead)
def transition_reddit_connector(
    connector_id: UUID,
    organization_id: UUID,
    payload: RedditConnectorUpdate,
    session: SessionDependency,
) -> RedditConnector:
    connector = scoped_reddit(session, RedditConnector, connector_id, organization_id)
    return RedditIntelligenceService(session).transition_connector(connector, payload.status)


@router.post(
    "/reddit-connectors/{connector_id}/ingest",
    response_model=RedditIngestionRead,
)
def ingest_reddit(
    connector_id: UUID,
    payload: RedditIngestionRequest,
    session: SessionDependency,
    transport: RedditTransportDependency,
) -> RedditIngestionRead:
    connector = scoped_reddit(session, RedditConnector, connector_id, payload.organization_id)
    job, candidate_count = RedditIntelligenceService(session).ingest(connector, payload, transport)
    return RedditIngestionRead(
        job_id=job.id,
        status=job.status,
        record_count=job.record_count,
        pain_candidate_count=candidate_count,
    )


@router.post("/pain-candidates", response_model=PainCandidateRead, status_code=201)
def create_pain_candidate(
    payload: PainCandidateCreate, session: SessionDependency
) -> CustomerPainCandidate:
    return RedditIntelligenceService(session).create_pain(payload)


@router.get("/pain-candidates", response_model=list[PainCandidateRead])
def list_pain_candidates(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerPainCandidate]:
    return _list(session, CustomerPainCandidate, organization_id)


@router.patch("/pain-candidates/{candidate_id}", response_model=PainCandidateRead)
def transition_pain_candidate(
    candidate_id: UUID,
    organization_id: UUID,
    payload: PainCandidateUpdate,
    session: SessionDependency,
) -> CustomerPainCandidate:
    candidate = scoped_reddit(session, CustomerPainCandidate, candidate_id, organization_id)
    return RedditIntelligenceService(session).transition_pain(candidate, payload.status)


@router.post("/pain-evidence", response_model=PainEvidenceRead, status_code=201)
def create_pain_evidence(payload: PainEvidenceCreate, session: SessionDependency) -> PainEvidence:
    return RedditIntelligenceService(session).link_evidence(payload)


@router.get("/pain-evidence", response_model=list[PainEvidenceRead])
def list_pain_evidence(organization_id: UUID, session: SessionDependency) -> list[PainEvidence]:
    return _list(session, PainEvidence, organization_id)
