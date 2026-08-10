from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.sales_support_models import (
    CustomerRiskSignal,
    RecommendationStatus,
    SalesIntelligenceProfile,
    SalesRecommendation,
    SupportCaseIntelligence,
)
from commerce_os.decision.sales_support_schemas import (
    RecommendationCreate,
    RiskSignalCreate,
    SalesProfileCreate,
    SupportIntelligenceCreate,
)
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
RECOMMENDATION_TRANSITIONS = {
    "draft": {"reviewed", "rejected"},
    "reviewed": {"accepted", "rejected"},
    "accepted": set(),
    "rejected": set(),
}


def scoped_recommendation(
    session: Session, entity_id: UUID, organization_id: UUID
) -> SalesRecommendation:
    entity = session.get(SalesRecommendation, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise DecisionScopeError("Sales recommendation was not found in this organization.")
    return entity


class SalesSupportDecisionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_profile(self, payload: SalesProfileCreate) -> SalesIntelligenceProfile:
        self._validate_reference(
            "customers", payload.customer_id, payload.organization_id, "Customer"
        )
        if payload.product_id:
            self._validate_reference(
                "products", payload.product_id, payload.organization_id, "Product"
            )
        threads = Base.metadata.tables["conversation_threads"]
        thread = self.session.execute(
            select(threads.c.id).where(
                threads.c.id == payload.conversation_id,
                threads.c.organization_id == payload.organization_id,
                threads.c.customer_id == payload.customer_id,
            )
        ).scalar_one_or_none()
        if thread is None:
            raise DecisionScopeError(
                "Conversation does not belong to this customer and organization."
            )
        messages = Base.metadata.tables["conversation_messages"]
        intents = Base.metadata.tables["conversation_intents"]
        observed_intent = self.session.execute(
            select(intents.c.id)
            .join(messages, intents.c.message_id == messages.c.id)
            .where(
                messages.c.thread_id == payload.conversation_id,
                intents.c.organization_id == payload.organization_id,
                intents.c.intent_type == payload.intent,
            )
            .limit(1)
        ).scalar_one_or_none()
        if observed_intent is None:
            raise DecisionScopeError("Sales profile intent requires conversation evidence.")
        return self._save(SalesIntelligenceProfile(**payload.model_dump()))

    def create_recommendation(self, payload: RecommendationCreate) -> SalesRecommendation:
        self._validate_reference(
            "sales_intelligence_profiles",
            payload.sales_profile_id,
            payload.organization_id,
            "Sales profile",
        )
        return self._save(
            SalesRecommendation(**payload.model_dump(), status=RecommendationStatus.DRAFT)
        )

    def transition_recommendation(
        self, recommendation: SalesRecommendation, status: RecommendationStatus
    ) -> SalesRecommendation:
        if status.value not in RECOMMENDATION_TRANSITIONS[str(recommendation.status)]:
            raise DecisionStateError(
                f"Recommendation cannot transition from {recommendation.status} to {status.value}."
            )
        recommendation.status = status
        return self._save(recommendation)

    def create_support(self, payload: SupportIntelligenceCreate) -> SupportCaseIntelligence:
        self._validate_reference(
            "conversation_threads",
            payload.conversation_id,
            payload.organization_id,
            "Conversation",
        )
        return self._save(SupportCaseIntelligence(**payload.model_dump()))

    def create_risk(self, payload: RiskSignalCreate) -> CustomerRiskSignal:
        self._validate_reference(
            "customers", payload.customer_id, payload.organization_id, "Customer"
        )
        return self._save(CustomerRiskSignal(**payload.model_dump()))

    def _validate_reference(
        self, table: str, reference_id: UUID, organization_id: UUID, label: str
    ) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name=table,
            reference_id=reference_id,
            organization_id=organization_id,
        ):
            raise DecisionScopeError(f"{label} was not found in this organization.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
