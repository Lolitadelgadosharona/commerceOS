from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.build.errors import BuildScopeError, BuildStateError
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
    CustomerQuestionCreate,
    ListingEvidenceCreate,
    ListingStrategyCreate,
    ProductDiscoveryKnowledgeCreate,
)
from commerce_os.build.models import Product, ProductTruth
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)

TRANSITIONS = {
    "draft": {"approved", "archived"},
    "approved": {"active", "archived"},
    "active": {"archived"},
    "archived": set(),
}


def require_product(session: Session, product_id: UUID, organization_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None or product.organization_id != organization_id:
        raise BuildScopeError("Product was not found in this organization.")
    return product


class ListingStrategyService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ListingStrategyCreate) -> ListingStrategy:
        require_product(self.session, payload.product_id, payload.organization_id)
        strategy = ListingStrategy(**payload.model_dump(), status=ListingStrategyStatus.DRAFT)
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return strategy

    def transition(
        self, strategy: ListingStrategy, status: ListingStrategyStatus
    ) -> ListingStrategy:
        if status.value not in TRANSITIONS[str(strategy.status)]:
            raise BuildStateError(
                f"Listing strategy cannot transition from {strategy.status} to {status.value}."
            )
        if status == ListingStrategyStatus.APPROVED:
            truth = self.session.scalar(
                select(ProductTruth.id)
                .where(ProductTruth.product_id == strategy.product_id)
                .limit(1)
            )
            if truth is None:
                raise BuildStateError("Product Truth is required before strategy approval.")
        strategy.status = status
        self.session.commit()
        self.session.refresh(strategy)
        return strategy


class ListingKnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_question(self, payload: CustomerQuestionCreate) -> CustomerQuestion:
        require_product(self.session, payload.product_id, payload.organization_id)
        value = CustomerQuestion(**payload.model_dump())
        return self._save(value)

    def create_discovery(
        self, payload: ProductDiscoveryKnowledgeCreate
    ) -> ProductDiscoveryKnowledge:
        require_product(self.session, payload.product_id, payload.organization_id)
        value = ProductDiscoveryKnowledge(**payload.model_dump())
        return self._save(value)

    def create_brief(self, payload: ContentBriefCreate) -> ContentBrief:
        require_product(self.session, payload.product_id, payload.organization_id)
        value = ContentBrief(**payload.model_dump())
        return self._save(value)

    def create_evidence(self, payload: ListingEvidenceCreate) -> ListingEvidence:
        require_product(self.session, payload.product_id, payload.organization_id)
        if payload.evidence_type == "specification":
            try:
                truth_id = UUID(payload.source_reference)
            except ValueError as error:
                raise BuildScopeError(
                    "Specification evidence requires a Product Truth UUID reference."
                ) from error
            truth = self.session.get(ProductTruth, truth_id)
            if (
                truth is None
                or truth.product_id != payload.product_id
                or truth.organization_id != payload.organization_id
            ):
                raise BuildScopeError("Product Truth evidence does not belong to this product.")
        value = ListingEvidence(**payload.model_dump())
        return self._save(value)

    def _save(self, value: EntityT) -> EntityT:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value
