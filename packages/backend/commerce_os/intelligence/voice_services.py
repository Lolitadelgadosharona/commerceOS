from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.connector_models import CustomerPainCandidate, MarketDataRecord
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.voice_models import (
    CustomerLanguageInsight,
    CustomerPainCluster,
    PainClusterMembership,
    PurchaseIntentSignal,
)
from commerce_os.intelligence.voice_schemas import (
    CustomerLanguageCreate,
    IntentScoreInputs,
    PainClusterCreate,
    PainMembershipCreate,
    PainScoreInputs,
    PurchaseIntentCreate,
)
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
CLUSTER_TRANSITIONS = {"draft": {"active", "archived"}, "active": {"archived"}, "archived": set()}


def scoped_voice(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError("Customer voice record was not found in this organization.")
    return entity


class CustomerVoiceService:
    pain_formula_version = "pain-severity-v1"
    intent_formula_version = "purchase-intent-v1"

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def pain_severity(inputs: PainScoreInputs) -> float:
        return round(
            inputs.frequency * 0.30
            + inputs.emotion * 0.25
            + inputs.urgency * 0.30
            + inputs.growth * 0.15,
            2,
        )

    @staticmethod
    def intent_score(inputs: IntentScoreInputs) -> float:
        return round(
            inputs.question_behavior * 0.20
            + inputs.solution_seeking * 0.35
            + inputs.purchase_language * 0.45,
            2,
        )

    def create_cluster(self, payload: PainClusterCreate) -> CustomerPainCluster:
        self._organization(payload.organization_id)
        evidence = payload.score_inputs.model_dump() | {"formula": self.pain_formula_version}
        values = payload.model_dump(exclude={"score_inputs"})
        return self._save(
            CustomerPainCluster(
                **values,
                severity_score=self.pain_severity(payload.score_inputs),
                scoring_evidence=evidence,
                status="draft",
            )
        )

    def transition_cluster(self, cluster: CustomerPainCluster, status: str) -> CustomerPainCluster:
        if status not in CLUSTER_TRANSITIONS[cluster.status]:
            raise IntelligenceValidationError(
                f"Pain cluster cannot transition from {cluster.status} to {status}."
            )
        cluster.status = status
        return self._save(cluster)

    def add_membership(
        self, cluster_id: UUID, payload: PainMembershipCreate
    ) -> PainClusterMembership:
        scoped_voice(self.session, CustomerPainCluster, cluster_id, payload.organization_id)
        scoped_voice(
            self.session,
            CustomerPainCandidate,
            payload.pain_candidate_id,
            payload.organization_id,
        )
        return self._save(PainClusterMembership(cluster_id=cluster_id, **payload.model_dump()))

    def create_language(self, payload: CustomerLanguageCreate) -> CustomerLanguageInsight:
        scoped_voice(self.session, CustomerPainCluster, payload.cluster_id, payload.organization_id)
        return self._save(CustomerLanguageInsight(**payload.model_dump()))

    def create_intent(self, payload: PurchaseIntentCreate) -> PurchaseIntentSignal:
        scoped_voice(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        evidence = payload.evidence | {
            "score_inputs": payload.score_inputs.model_dump(),
            "formula": self.intent_formula_version,
        }
        values = payload.model_dump(exclude={"score_inputs", "evidence"})
        return self._save(
            PurchaseIntentSignal(
                **values,
                evidence=evidence,
                intent_score=self.intent_score(payload.score_inputs),
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
