import hashlib
import json
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.connector_models import (
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
)
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.marketplace_models import (
    CompetitiveMarketplaceObservation,
    MarketplaceEvidenceLink,
    MarketplaceReviewEvidence,
    NormalizedMarketplaceReview,
)
from commerce_os.intelligence.marketplace_schemas import (
    CompetitiveObservationCreate,
    MarketplaceEvidenceLinkCreate,
    MarketplaceReviewCreate,
    NormalizedMarketplaceReviewCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
TARGET_TABLES = {
    "customer_signal": "customer_signals",
    "pain_cluster": "customer_pain_clusters",
    "customer_language": "customer_language_insights",
    "opportunity_evidence": "opportunity_evidence",
}


def scoped_marketplace(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Marketplace intelligence record was not found in this organization."
        )
    return entity


class MarketplaceVoiceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def capture_review(
        self, payload: MarketplaceReviewCreate, actor_id: UUID | None = None
    ) -> MarketplaceReviewEvidence:
        connector = scoped_marketplace(
            self.session, MarketConnectorDefinition, payload.connector_id, payload.organization_id
        )
        if connector.connector_type not in {"amazon", "etsy", "marketplace"}:
            raise IntelligenceValidationError("Review evidence requires a marketplace connector.")
        if connector.status not in {"ready", "active"}:
            raise IntelligenceValidationError(
                "Review evidence requires a ready marketplace connector."
            )
        if connector.platform.lower() != payload.marketplace:
            raise IntelligenceValidationError(
                "Review marketplace must match the connector platform."
            )
        raw = scoped_marketplace(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        if raw.source_id != connector.id:
            raise IntelligenceValidationError("Raw evidence must belong to the selected connector.")
        if payload.ingestion_job_id is not None:
            job = scoped_marketplace(
                self.session, MarketIngestionJob, payload.ingestion_job_id, payload.organization_id
            )
            if job.source_id != connector.id:
                raise IntelligenceValidationError(
                    "Ingestion job must belong to the selected connector."
                )
        self._reject_secret_material(payload.review_text_metadata)
        evidence_hash = self._hash(payload, raw.payload_hash)
        existing = self.session.scalar(
            select(MarketplaceReviewEvidence).where(
                MarketplaceReviewEvidence.organization_id == payload.organization_id,
                MarketplaceReviewEvidence.marketplace == payload.marketplace,
                MarketplaceReviewEvidence.source_identity == payload.source_identity,
            )
        )
        if existing is not None:
            if existing.evidence_hash != evidence_hash:
                raise IntelligenceValidationError(
                    "Source identity already identifies different immutable review evidence."
                )
            return existing
        duplicate = self.session.scalar(
            select(MarketplaceReviewEvidence).where(
                MarketplaceReviewEvidence.organization_id == payload.organization_id,
                MarketplaceReviewEvidence.evidence_hash == evidence_hash,
            )
        )
        if duplicate is not None:
            return duplicate
        return self._save_audited(
            MarketplaceReviewEvidence(**payload.model_dump(), evidence_hash=evidence_hash),
            actor_id,
            "marketplace.review_evidence.captured",
        )

    def normalize(
        self, payload: NormalizedMarketplaceReviewCreate, actor_id: UUID | None = None
    ) -> NormalizedMarketplaceReview:
        scoped_marketplace(
            self.session,
            MarketplaceReviewEvidence,
            payload.review_evidence_id,
            payload.organization_id,
        )
        self._reject_secret_material(payload.sentiment_metadata)
        self._reject_secret_material(payload.topic_metadata)
        if self.session.scalar(
            select(NormalizedMarketplaceReview).where(
                NormalizedMarketplaceReview.review_evidence_id == payload.review_evidence_id
            )
        ):
            raise IntelligenceValidationError(
                "Review evidence already has a normalized customer voice record."
            )
        return self._save_audited(
            NormalizedMarketplaceReview(**payload.model_dump()),
            actor_id,
            "marketplace.review.normalized",
        )

    def link_evidence(
        self, payload: MarketplaceEvidenceLinkCreate, actor_id: UUID | None = None
    ) -> MarketplaceEvidenceLink:
        scoped_marketplace(
            self.session,
            MarketplaceReviewEvidence,
            payload.review_evidence_id,
            payload.organization_id,
        )
        table = Base.metadata.tables[TARGET_TABLES[payload.target_type]]
        target = self.session.execute(
            select(table.c.id).where(
                table.c.id == payload.target_id, table.c.organization_id == payload.organization_id
            )
        ).scalar_one_or_none()
        if target is None:
            raise IntelligenceScopeError("Evidence target was not found in this organization.")
        return self._save_audited(
            MarketplaceEvidenceLink(**payload.model_dump()), actor_id, "marketplace.evidence.linked"
        )

    def create_competitive_observation(
        self, payload: CompetitiveObservationCreate, actor_id: UUID | None = None
    ) -> CompetitiveMarketplaceObservation:
        scoped_marketplace(
            self.session,
            MarketplaceReviewEvidence,
            payload.review_evidence_id,
            payload.organization_id,
        )
        self._reject_secret_material(payload.product_observations)
        return self._save_audited(
            CompetitiveMarketplaceObservation(**payload.model_dump()),
            actor_id,
            "marketplace.competitive_observation.created",
        )

    def _save_audited(self, entity: EntityT, actor_id: UUID | None, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type="human" if actor_id else "system",
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=cast(UUID, entity.id),  # type: ignore[attr-defined]
            metadata={"result": "success"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity

    @staticmethod
    def _hash(payload: MarketplaceReviewCreate, raw_hash: str) -> str:
        canonical = json.dumps(
            {
                "raw_hash": raw_hash,
                "marketplace": payload.marketplace,
                "source_identity": payload.source_identity,
                "product_reference": payload.product_reference,
                "rating": payload.rating,
                "review_date": payload.review_date.isoformat(),
                "review_text_metadata": payload.review_text_metadata,
                "verified_indicator": payload.verified_indicator,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def _reject_secret_material(cls, value: Any) -> None:
        forbidden = {"secret", "password", "token", "api_key", "private_key", "credential"}
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in forbidden or normalized.endswith("_secret"):
                    raise IntelligenceValidationError(
                        "Marketplace evidence may contain credential references, "
                        "never secret material."
                    )
                cls._reject_secret_material(item)
        elif isinstance(value, list):
            for item in value:
                cls._reject_secret_material(item)
