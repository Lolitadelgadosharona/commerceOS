import hashlib
import json
from datetime import UTC, datetime
from typing import Any, TypeVar, cast
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
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
CONNECTOR_TRANSITIONS = {
    "draft": {"configured", "disabled", "active"},
    "configured": {"ready", "disabled"},
    "ready": {"disabled"},
    "disabled": set(),
    "inactive": {"active", "archived"},
    "active": {"inactive", "archived"},
    "archived": set(),
}
JOB_TRANSITIONS = {
    "draft": {"configured", "disabled"},
    "configured": {"ready", "disabled"},
    "ready": {"running", "disabled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "pending": {"running"},
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

    def create_connector(
        self, payload: ConnectorCreate, actor_id: UUID | None = None
    ) -> MarketConnectorDefinition:
        self._organization(payload.organization_id)
        self._reject_secret_material(payload.configuration_schema)
        self._reject_secret_material(payload.rate_limit_metadata)
        if (
            payload.authentication_state in {"reference_configured", "verified"}
            and payload.credential_reference is None
        ):
            raise IntelligenceValidationError(
                "Configured authentication requires an external credential reference."
            )
        return self._save_audited(
            MarketConnectorDefinition(**payload.model_dump(), status="draft"),
            actor_id,
            "connector.created",
        )

    def transition_connector(
        self, connector: MarketConnectorDefinition, status: str, actor_id: UUID | None = None
    ) -> MarketConnectorDefinition:
        if status not in CONNECTOR_TRANSITIONS[connector.status]:
            raise IntelligenceValidationError(
                f"Connector cannot transition from {connector.status} to {status}."
            )
        if status == "ready" and connector.authentication_state not in {
            "not_required",
            "verified",
        }:
            raise IntelligenceValidationError(
                "Ready connectors require a credential reference or explicit no-auth state."
            )
        connector.status = status
        return self._save_audited(connector, actor_id, f"connector.{status}")

    def store_record(
        self, payload: MarketDataRecordCreate, actor_id: UUID | None = None
    ) -> MarketDataRecord:
        connector = scoped_connector(
            self.session, MarketConnectorDefinition, payload.source_id, payload.organization_id
        )
        if connector.status not in {"ready", "active"}:
            raise IntelligenceValidationError("Raw records require a ready connector definition.")
        self._reject_secret_material(payload.metadata)
        payload_hash = self._payload_hash(payload)
        idempotency_key = payload.idempotency_key or payload.external_reference
        existing_key = self.session.scalar(
            select(MarketDataRecord).where(
                MarketDataRecord.organization_id == payload.organization_id,
                MarketDataRecord.source_id == payload.source_id,
                MarketDataRecord.idempotency_key == idempotency_key,
            )
        )
        if existing_key is not None:
            if existing_key.payload_hash != payload_hash:
                raise IntelligenceValidationError(
                    "Idempotency key already identifies different immutable evidence."
                )
            return existing_key
        existing_hash = self.session.scalar(
            select(MarketDataRecord).where(
                MarketDataRecord.organization_id == payload.organization_id,
                MarketDataRecord.source_id == payload.source_id,
                MarketDataRecord.payload_hash == payload_hash,
            )
        )
        if existing_hash is not None:
            return existing_hash
        values = payload.model_dump(exclude={"metadata", "idempotency_key"})
        return self._save_audited(
            MarketDataRecord(
                **values,
                metadata_json=payload.metadata,
                payload_hash=payload_hash,
                idempotency_key=idempotency_key,
            ),
            actor_id,
            "connector.raw_evidence.captured",
        )

    def normalize(
        self, payload: NormalizedMarketItemCreate, actor_id: UUID | None = None
    ) -> NormalizedMarketItem:
        scoped_connector(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        self._reject_secret_material(payload.relevance_metadata)
        return self._save_audited(
            NormalizedMarketItem(**payload.model_dump()),
            actor_id,
            "connector.evidence.normalized",
        )

    def create_job(
        self, payload: IngestionJobCreate, actor_id: UUID | None = None
    ) -> MarketIngestionJob:
        connector = scoped_connector(
            self.session, MarketConnectorDefinition, payload.source_id, payload.organization_id
        )
        if connector.status not in {"ready", "active"}:
            raise IntelligenceValidationError(
                "Ingestion jobs require a ready connector definition."
            )
        initial_status = "pending" if connector.status == "active" else "draft"
        return self._save_audited(
            MarketIngestionJob(
                **payload.model_dump(), status=initial_status, record_count=0, errors=[]
            ),
            actor_id,
            "connector.ingestion.created",
        )

    def transition_job(
        self,
        job: MarketIngestionJob,
        payload: IngestionJobUpdate,
        actor_id: UUID | None = None,
    ) -> MarketIngestionJob:
        if payload.status not in JOB_TRANSITIONS[job.status]:
            raise IntelligenceValidationError(
                f"Ingestion job cannot transition from {job.status} to {payload.status}."
            )
        now = datetime.now(UTC)
        if payload.status == "running":
            job.started_at = now
        elif payload.status in {"completed", "failed", "disabled"}:
            job.completed_at = now
        if payload.record_count is not None:
            job.record_count = payload.record_count
        if payload.errors is not None:
            job.errors = payload.errors
        job.status = payload.status
        return self._save_audited(job, actor_id, f"connector.ingestion.{payload.status}")

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

    def _save_audited(self, entity: EntityT, actor_id: UUID | None, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type="human" if actor_id is not None else "system",
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=entity_id(entity),
            metadata={"result": "success"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity

    @staticmethod
    def _payload_hash(payload: MarketDataRecordCreate) -> str:
        canonical = json.dumps(
            {
                "source_reference": payload.external_reference,
                "content_type": payload.content_type,
                "raw_content": payload.raw_content,
                "metadata": payload.metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def _reject_secret_material(cls, value: Any, path: str = "metadata") -> None:
        forbidden = {"secret", "password", "token", "api_key", "private_key", "credential"}
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in forbidden or normalized.endswith("_secret"):
                    raise IntelligenceValidationError(
                        f"Secret material is forbidden in {path}; store only secret references."
                    )
                cls._reject_secret_material(item, f"{path}.{key}")
        elif isinstance(value, list):
            for item in value:
                cls._reject_secret_material(item, path)


def entity_id(entity: Any) -> UUID:
    return cast(UUID, entity.id)
