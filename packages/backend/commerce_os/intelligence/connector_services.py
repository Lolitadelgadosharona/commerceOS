from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.connector_models import (
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
    NormalizedMarketItem,
)
from commerce_os.intelligence.connector_schemas import (
    ConnectorCreate,
    IngestionJobCreate,
    IngestionJobUpdate,
    MarketDataRecordCreate,
    NormalizedMarketItemCreate,
)
from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
CONNECTOR_TRANSITIONS = {
    "inactive": {"active", "archived"},
    "active": {"inactive", "archived"},
    "archived": set(),
}
JOB_TRANSITIONS = {
    "pending": {"running"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


def scoped_connector(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError("Connector record was not found in this organization.")
    return entity


class MarketConnectorService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_connector(self, payload: ConnectorCreate) -> MarketConnectorDefinition:
        self._organization(payload.organization_id)
        return self._save(MarketConnectorDefinition(**payload.model_dump(), status="inactive"))

    def transition_connector(
        self, connector: MarketConnectorDefinition, status: str
    ) -> MarketConnectorDefinition:
        if status not in CONNECTOR_TRANSITIONS[connector.status]:
            raise IntelligenceValidationError(
                f"Connector cannot transition from {connector.status} to {status}."
            )
        connector.status = status
        return self._save(connector)

    def store_record(self, payload: MarketDataRecordCreate) -> MarketDataRecord:
        connector = scoped_connector(
            self.session, MarketConnectorDefinition, payload.source_id, payload.organization_id
        )
        if connector.status != "active":
            raise IntelligenceValidationError("Raw records require an active connector definition.")
        values = payload.model_dump(exclude={"metadata"})
        return self._save(MarketDataRecord(**values, metadata_json=payload.metadata))

    def normalize(self, payload: NormalizedMarketItemCreate) -> NormalizedMarketItem:
        scoped_connector(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        return self._save(NormalizedMarketItem(**payload.model_dump()))

    def create_job(self, payload: IngestionJobCreate) -> MarketIngestionJob:
        connector = scoped_connector(
            self.session, MarketConnectorDefinition, payload.source_id, payload.organization_id
        )
        if connector.status != "active":
            raise IntelligenceValidationError(
                "Ingestion jobs require an active connector definition."
            )
        return self._save(
            MarketIngestionJob(**payload.model_dump(), status="pending", record_count=0)
        )

    def transition_job(
        self, job: MarketIngestionJob, payload: IngestionJobUpdate
    ) -> MarketIngestionJob:
        if payload.status not in JOB_TRANSITIONS[job.status]:
            raise IntelligenceValidationError(
                f"Ingestion job cannot transition from {job.status} to {payload.status}."
            )
        now = datetime.now(UTC)
        if payload.status == "running":
            job.started_at = now
        else:
            job.completed_at = now
        if payload.record_count is not None:
            job.record_count = payload.record_count
        job.status = payload.status
        return self._save(job)

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        exists = self.session.execute(
            select(table.c.id).where(table.c.id == organization_id)
        ).scalar_one_or_none()
        if exists is None:
            raise IntelligenceNotFoundError("Organization was not found.")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
