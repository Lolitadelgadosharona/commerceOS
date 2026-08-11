from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.need_models import (
    CustomerBackedOpportunityAssessment,
    CustomerNeed,
    PainNeedMapping,
    ProductSolutionHypothesis,
)
from commerce_os.intelligence.need_schemas import (
    CustomerBackedAssessmentCreate,
    CustomerNeedCreate,
    PainNeedMappingCreate,
    ProductSolutionCreate,
)
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.intelligence.voice_models import CustomerPainCluster, PainClusterMembership
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
NEED_TRANSITIONS = {
    "draft": {"validated", "archived"},
    "validated": {"archived"},
    "archived": set(),
}


def scoped_need(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Product opportunity evidence was not found in this organization."
        )
    return entity


class CustomerNeedService:
    formula_version = "customer-backed-opportunity-v1"

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def overall(payload: CustomerBackedAssessmentCreate) -> float:
        return round(
            payload.pain_strength * 0.25
            + payload.solution_fit * 0.25
            + payload.intent_score * 0.15
            + payload.competition_score * 0.10
            + payload.margin_score * 0.15
            + (100 - payload.risk_score) * 0.10,
            2,
        )

    def create_need(self, payload: CustomerNeedCreate) -> CustomerNeed:
        self._organization(payload.organization_id)
        return self._save(CustomerNeed(**payload.model_dump(), status="draft"))

    def transition_need(self, need: CustomerNeed, status: str) -> CustomerNeed:
        if status not in NEED_TRANSITIONS[need.status]:
            raise IntelligenceValidationError(
                f"Customer need cannot transition from {need.status} to {status}."
            )
        need.status = status
        return self._save(need)

    def map_pain(self, payload: PainNeedMappingCreate) -> PainNeedMapping:
        scoped_need(
            self.session, CustomerPainCluster, payload.pain_cluster_id, payload.organization_id
        )
        scoped_need(self.session, CustomerNeed, payload.need_id, payload.organization_id)
        actual = self.session.scalar(
            select(func.count())
            .select_from(PainClusterMembership)
            .where(
                PainClusterMembership.organization_id == payload.organization_id,
                PainClusterMembership.cluster_id == payload.pain_cluster_id,
            )
        )
        if actual != payload.evidence_count:
            raise IntelligenceValidationError(
                "Evidence count must equal source-traceable cluster membership count."
            )
        return self._save(PainNeedMapping(**payload.model_dump()))

    def create_solution(self, payload: ProductSolutionCreate) -> ProductSolutionHypothesis:
        scoped_need(self.session, CustomerNeed, payload.need_id, payload.organization_id)
        return self._save(ProductSolutionHypothesis(**payload.model_dump()))

    def assess(
        self, payload: CustomerBackedAssessmentCreate
    ) -> CustomerBackedOpportunityAssessment:
        scoped_need(
            self.session, MarketOpportunity, payload.opportunity_id, payload.organization_id
        )
        scoped_need(self.session, CustomerNeed, payload.need_id, payload.organization_id)
        mapping = self.session.scalar(
            select(PainNeedMapping).where(
                PainNeedMapping.organization_id == payload.organization_id,
                PainNeedMapping.need_id == payload.need_id,
            )
        )
        solution = self.session.scalar(
            select(ProductSolutionHypothesis).where(
                ProductSolutionHypothesis.organization_id == payload.organization_id,
                ProductSolutionHypothesis.need_id == payload.need_id,
            )
        )
        if mapping is None or solution is None:
            raise IntelligenceValidationError(
                "Assessment requires pain mapping and solution evidence."
            )
        return self._save(
            CustomerBackedOpportunityAssessment(
                **payload.model_dump(),
                overall_score=self.overall(payload),
                formula_version=self.formula_version,
            )
        )

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if self.session.scalar(select(table.c.id).where(table.c.id == organization_id)) is None:
            raise IntelligenceScopeError("Organization was not found.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
