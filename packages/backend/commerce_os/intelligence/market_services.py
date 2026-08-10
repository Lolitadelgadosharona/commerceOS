from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.market_models import (
    MarketDataSource,
    MarketSignal,
    MarketSignalCluster,
    MarketSignalClusterMembership,
    MarketSignalEvidence,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.market_schemas import (
    MarketClusterCreate,
    MarketEvidenceCreate,
    MarketSignalCreate,
    MarketSourceCreate,
)
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
SOURCE_TRANSITIONS = {
    "inactive": {"active", "archived"},
    "active": {"inactive", "archived"},
    "archived": set(),
}
SIGNAL_TRANSITIONS = {
    "observed": {"validated", "archived"},
    "validated": {"archived"},
    "archived": set(),
}


def scoped_market(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Market intelligence record was not found in this organization."
        )
    return entity


class MarketIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_source(self, payload: MarketSourceCreate) -> MarketDataSource:
        self._organization(payload.organization_id)
        return self._save(MarketDataSource(**payload.model_dump(), status="inactive"))

    def transition_source(self, source: MarketDataSource, status: str) -> MarketDataSource:
        if status not in SOURCE_TRANSITIONS[source.status]:
            raise IntelligenceValidationError(
                f"Market source cannot transition from {source.status} to {status}."
            )
        source.status = status
        return self._save(source)

    def create_signal(self, payload: MarketSignalCreate) -> MarketSignal:
        source = scoped_market(
            self.session, MarketDataSource, payload.source_id, payload.organization_id
        )
        if source.status != "active":
            raise IntelligenceValidationError("Market signals require an active registered source.")
        return self._save(MarketSignal(**payload.model_dump(), status="observed"))

    def transition_signal(self, signal: MarketSignal, status: str) -> MarketSignal:
        if status not in SIGNAL_TRANSITIONS[signal.status]:
            raise IntelligenceValidationError(
                f"Market signal cannot transition from {signal.status} to {status}."
            )
        signal.status = status
        return self._save(signal)

    def add_evidence(self, payload: MarketEvidenceCreate) -> MarketSignalEvidence:
        scoped_market(self.session, MarketSignal, payload.signal_id, payload.organization_id)
        return self._save(MarketSignalEvidence(**payload.model_dump()))

    def create_cluster(self, payload: MarketClusterCreate) -> MarketSignalCluster:
        self._organization(payload.organization_id)
        return self._save(MarketSignalCluster(**payload.model_dump()))

    def add_to_cluster(
        self, cluster_id: UUID, signal_id: UUID, organization_id: UUID
    ) -> MarketSignalClusterMembership:
        scoped_market(self.session, MarketSignalCluster, cluster_id, organization_id)
        scoped_market(self.session, MarketSignal, signal_id, organization_id)
        return self._save(
            MarketSignalClusterMembership(
                organization_id=organization_id, cluster_id=cluster_id, signal_id=signal_id
            )
        )

    def link_opportunity(
        self, signal_id: UUID, opportunity_id: UUID, organization_id: UUID
    ) -> MarketSignalOpportunityLink:
        scoped_market(self.session, MarketSignal, signal_id, organization_id)
        if not reference_belongs_to_organization(
            self.session,
            table_name="market_opportunities",
            reference_id=opportunity_id,
            organization_id=organization_id,
        ):
            raise IntelligenceScopeError("Market opportunity was not found in this organization.")
        return self._save(
            MarketSignalOpportunityLink(
                organization_id=organization_id,
                signal_id=signal_id,
                opportunity_id=opportunity_id,
            )
        )

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if (
            self.session.execute(
                select(table.c.id).where(table.c.id == organization_id)
            ).scalar_one_or_none()
            is None
        ):
            raise IntelligenceNotFoundError("Organization was not found.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
