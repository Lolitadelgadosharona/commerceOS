import json
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
    PainEvidence,
    RedditConnector,
)
from commerce_os.intelligence.connector_services import scoped_connector
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.reddit_client import RedditItem, RedditReadTransport
from commerce_os.intelligence.reddit_schemas import (
    PainCandidateCreate,
    PainEvidenceCreate,
    RedditConnectorCreate,
    RedditIngestionRequest,
)
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
REDDIT_TRANSITIONS = {
    "inactive": {"active", "archived"},
    "active": {"inactive", "archived"},
    "archived": set(),
}
PAIN_TRANSITIONS = {
    "detected": {"reviewed", "accepted", "rejected"},
    "reviewed": {"accepted", "rejected"},
    "accepted": set(),
    "rejected": set(),
}
PAIN_TERMS = {
    "complaint": ("complaint", "broken", "terrible", "awful", "hate"),
    "frustration": ("frustrated", "annoying", "struggle", "difficult"),
    "request": ("please add", "feature request", "could you", "need a"),
    "want": ("i want", "wish", "looking for", "would love"),
    "problem": ("problem", "issue", "doesn't work", "cannot", "can't"),
}


def scoped_reddit(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise IntelligenceScopeError(
            "Reddit intelligence record was not found in this organization."
        )
    return entity


class RedditIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_connector(self, payload: RedditConnectorCreate) -> RedditConnector:
        organization = Base.metadata.tables["organizations"]
        if (
            self.session.scalar(
                select(organization.c.id).where(organization.c.id == payload.organization_id)
            )
            is None
        ):
            raise IntelligenceScopeError("Organization was not found.")
        definition = self._save(
            MarketConnectorDefinition(
                organization_id=payload.organization_id,
                name=payload.name,
                platform="reddit",
                connector_type="reddit",
                status="inactive",
                configuration_schema={
                    "subreddit_scope": payload.subreddit_scope,
                    "keyword_scope": payload.keyword_scope,
                    "time_window": payload.time_window,
                    "credentials": "external_environment",
                    "capabilities": ["read_posts", "read_comments", "store_metadata"],
                },
            )
        )
        return self._save(
            RedditConnector(
                organization_id=payload.organization_id,
                connector_definition_id=definition.id,
                subreddit_scope=payload.subreddit_scope,
                keyword_scope=payload.keyword_scope,
                time_window=payload.time_window,
                status="inactive",
            )
        )

    def transition_connector(self, connector: RedditConnector, status: str) -> RedditConnector:
        if status not in REDDIT_TRANSITIONS[connector.status]:
            raise IntelligenceValidationError(
                f"Reddit connector cannot transition from {connector.status} to {status}."
            )
        definition = scoped_connector(
            self.session,
            MarketConnectorDefinition,
            connector.connector_definition_id,
            connector.organization_id,
        )
        connector.status = status
        definition.status = status
        self.session.add_all([connector, definition])
        self.session.commit()
        self.session.refresh(connector)
        return connector

    def ingest(
        self,
        connector: RedditConnector,
        payload: RedditIngestionRequest,
        transport: RedditReadTransport,
    ) -> tuple[MarketIngestionJob, int]:
        if connector.status != "active":
            raise IntelligenceValidationError("Reddit ingestion requires an active connector.")
        job = self._save(
            MarketIngestionJob(
                organization_id=payload.organization_id,
                source_id=connector.connector_definition_id,
                source_platform="reddit",
                status="running",
                started_at=datetime.now(UTC),
                record_count=0,
            )
        )
        candidate_count = 0
        record_count = 0
        try:
            for subreddit in connector.subreddit_scope:
                posts = transport.read_posts(
                    subreddit, connector.time_window, payload.limit_per_subreddit
                )
                for post in posts:
                    stored, detected = self._store_and_detect(connector, post)
                    record_count += stored
                    candidate_count += detected
                    if payload.include_comments and payload.comments_per_post:
                        for comment in transport.read_comments(
                            post.external_id, subreddit, payload.comments_per_post
                        ):
                            stored, detected = self._store_and_detect(connector, comment)
                            record_count += stored
                            candidate_count += detected
            job.status = "completed"
            job.completed_at = datetime.now(UTC)
            job.record_count = record_count
        except Exception:
            job.status = "failed"
            job.completed_at = datetime.now(UTC)
            self._save(job)
            raise
        return self._save(job), candidate_count

    def create_pain(self, payload: PainCandidateCreate) -> CustomerPainCandidate:
        record = scoped_reddit(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        if record.source_platform != "reddit":
            raise IntelligenceValidationError("Pain candidates require a Reddit source record.")
        return self._save(CustomerPainCandidate(**payload.model_dump(), status="detected"))

    def transition_pain(
        self, candidate: CustomerPainCandidate, status: str
    ) -> CustomerPainCandidate:
        if status not in PAIN_TRANSITIONS[candidate.status]:
            raise IntelligenceValidationError(
                f"Pain candidate cannot transition from {candidate.status} to {status}."
            )
        candidate.status = status
        return self._save(candidate)

    def link_evidence(self, payload: PainEvidenceCreate) -> PainEvidence:
        candidate = scoped_reddit(
            self.session,
            CustomerPainCandidate,
            payload.pain_candidate_id,
            payload.organization_id,
        )
        record = scoped_reddit(
            self.session, MarketDataRecord, payload.source_record_id, payload.organization_id
        )
        if candidate.source_record_id != record.id:
            raise IntelligenceValidationError(
                "Pain evidence must reference the candidate's source record in V1."
            )
        return self._save(PainEvidence(**payload.model_dump()))

    def _store_and_detect(self, connector: RedditConnector, item: RedditItem) -> tuple[int, int]:
        text = " ".join(part for part in (item.title, item.content) if part).strip()
        if not self._keyword_match(text, connector.keyword_scope):
            return 0, 0
        existing = self.session.scalar(
            select(MarketDataRecord)
            .where(MarketDataRecord.organization_id == connector.organization_id)
            .where(MarketDataRecord.source_id == connector.connector_definition_id)
            .where(MarketDataRecord.external_id == item.external_id)
        )
        if existing is not None:
            return 0, 0
        record = self._save(
            MarketDataRecord(
                organization_id=connector.organization_id,
                source_id=connector.connector_definition_id,
                source_platform="reddit",
                external_reference=f"https://reddit.com{item.permalink}",
                external_id=item.external_id,
                content_type=item.kind,
                raw_content=json.dumps({"title": item.title, "content": item.content}),
                metadata_json={"source": "reddit", "kind": item.kind},
                captured_at=datetime.now(UTC),
                subreddit=item.subreddit,
                title=item.title,
                content=item.content,
                author_reference=item.author_reference,
                engagement_metrics={
                    "score": item.score,
                    "comment_count": item.comment_count,
                },
                published_at=datetime.fromtimestamp(item.published_timestamp, UTC),
            )
        )
        category, confidence = self._classify(text)
        if category is None:
            return 1, 0
        candidate = self.create_pain(
            PainCandidateCreate(
                organization_id=connector.organization_id,
                source_record_id=record.id,
                pain_category=category,
                customer_language=text,
                confidence_score=confidence,
            )
        )
        self.link_evidence(
            PainEvidenceCreate(
                organization_id=connector.organization_id,
                pain_candidate_id=candidate.id,
                source_record_id=record.id,
                evidence_strength=confidence,
            )
        )
        return 1, 1

    @staticmethod
    def _keyword_match(text: str, keywords: list[str]) -> bool:
        lowered = text.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    @staticmethod
    def _classify(text: str) -> tuple[str | None, float]:
        lowered = text.lower()
        for category, terms in PAIN_TERMS.items():
            matches = sum(term in lowered for term in terms)
            if matches:
                return category, min(0.55 + matches * 0.1, 0.95)
        return None, 0.0

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
