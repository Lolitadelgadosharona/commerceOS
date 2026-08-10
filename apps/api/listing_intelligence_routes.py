from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.build.errors import BuildNotFoundError, BuildScopeError
from commerce_os.build.listing_models import (
    ContentBrief,
    CustomerQuestion,
    ListingEvidence,
    ListingStrategy,
    ListingStrategyStatus,
    ProductDiscoveryKnowledge,
)
from commerce_os.build.listing_schemas import (
    ContentBriefCreate,
    ContentBriefRead,
    CustomerQuestionCreate,
    CustomerQuestionRead,
    ListingEvidenceCreate,
    ListingEvidenceRead,
    ListingStrategyCreate,
    ListingStrategyRead,
    ListingStrategyUpdate,
    ProductDiscoveryKnowledgeCreate,
    ProductDiscoveryKnowledgeRead,
)
from commerce_os.build.listing_services import ListingKnowledgeService, ListingStrategyService
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


def _strategy(session: Session, strategy_id: UUID, organization_id: UUID) -> ListingStrategy:
    strategy = session.get(ListingStrategy, strategy_id)
    if strategy is None:
        raise BuildNotFoundError("Listing strategy was not found.")
    if strategy.organization_id != organization_id:
        raise BuildScopeError("Listing strategy belongs to another organization.")
    return strategy


@router.post(
    "/listing-strategies",
    response_model=ListingStrategyRead,
    status_code=201,
    tags=["listing_strategies"],
)
def create_strategy(payload: ListingStrategyCreate, session: SessionDependency) -> ListingStrategy:
    return ListingStrategyService(session).create(payload)


@router.get(
    "/listing-strategies", response_model=list[ListingStrategyRead], tags=["listing_strategies"]
)
def list_strategies(organization_id: UUID, session: SessionDependency) -> list[ListingStrategy]:
    return _list(session, ListingStrategy, organization_id)


@router.patch(
    "/listing-strategies/{strategy_id}",
    response_model=ListingStrategyRead,
    tags=["listing_strategies"],
)
def transition_strategy(
    strategy_id: UUID,
    organization_id: UUID,
    payload: ListingStrategyUpdate,
    session: SessionDependency,
) -> ListingStrategy:
    return ListingStrategyService(session).transition(
        _strategy(session, strategy_id, organization_id), ListingStrategyStatus(payload.status)
    )


@router.post(
    "/customer-questions",
    response_model=CustomerQuestionRead,
    status_code=201,
    tags=["customer_questions"],
)
def create_question(
    payload: CustomerQuestionCreate, session: SessionDependency
) -> CustomerQuestion:
    return ListingKnowledgeService(session).create_question(payload)


@router.get(
    "/customer-questions", response_model=list[CustomerQuestionRead], tags=["customer_questions"]
)
def list_questions(organization_id: UUID, session: SessionDependency) -> list[CustomerQuestion]:
    return _list(session, CustomerQuestion, organization_id)


@router.post(
    "/product-discovery-knowledge",
    response_model=ProductDiscoveryKnowledgeRead,
    status_code=201,
    tags=["product_discovery_knowledge"],
)
def create_discovery(
    payload: ProductDiscoveryKnowledgeCreate, session: SessionDependency
) -> ProductDiscoveryKnowledge:
    return ListingKnowledgeService(session).create_discovery(payload)


@router.get(
    "/product-discovery-knowledge",
    response_model=list[ProductDiscoveryKnowledgeRead],
    tags=["product_discovery_knowledge"],
)
def list_discovery(
    organization_id: UUID, session: SessionDependency
) -> list[ProductDiscoveryKnowledge]:
    return _list(session, ProductDiscoveryKnowledge, organization_id)


@router.post(
    "/content-briefs", response_model=ContentBriefRead, status_code=201, tags=["content_briefs"]
)
def create_brief(payload: ContentBriefCreate, session: SessionDependency) -> ContentBrief:
    return ListingKnowledgeService(session).create_brief(payload)


@router.get("/content-briefs", response_model=list[ContentBriefRead], tags=["content_briefs"])
def list_briefs(organization_id: UUID, session: SessionDependency) -> list[ContentBrief]:
    return _list(session, ContentBrief, organization_id)


@router.post(
    "/listing-evidence",
    response_model=ListingEvidenceRead,
    status_code=201,
    tags=["listing_evidence"],
)
def create_evidence(payload: ListingEvidenceCreate, session: SessionDependency) -> ListingEvidence:
    return ListingKnowledgeService(session).create_evidence(payload)


@router.get(
    "/listing-evidence", response_model=list[ListingEvidenceRead], tags=["listing_evidence"]
)
def list_evidence(organization_id: UUID, session: SessionDependency) -> list[ListingEvidence]:
    return _list(session, ListingEvidence, organization_id)
