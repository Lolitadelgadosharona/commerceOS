from datetime import UTC, datetime

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    MarketDataRecord,
    MarketIngestionJob,
    PainEvidence,
)
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.reddit_client import RedditItem
from commerce_os.intelligence.reddit_schemas import PainCandidateCreate
from commerce_os.intelligence.reddit_services import RedditIntelligenceService
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.api.reddit_intelligence_routes import get_reddit_transport


class FakeRedditTransport:
    def read_posts(self, subreddit: str, time_window: str, limit: int) -> list[RedditItem]:
        assert time_window == "week"
        return [
            RedditItem(
                external_id="post-1",
                kind="post",
                subreddit=subreddit,
                title="I have a problem with cooling",
                content="This fan doesn't work and I want a quieter one.",
                author_reference="t2_author",
                score=42,
                comment_count=1,
                published_timestamp=datetime(2026, 8, 10, tzinfo=UTC).timestamp(),
                permalink="/r/home/comments/post-1/example/",
            )
        ][:limit]

    def read_comments(self, post_id: str, subreddit: str, limit: int) -> list[RedditItem]:
        assert post_id == "post-1"
        return [
            RedditItem(
                external_id="comment-1",
                kind="comment",
                subreddit=subreddit,
                title="",
                content="I am frustrated by the same fan problem.",
                author_reference=None,
                score=3,
                comment_count=0,
                published_timestamp=datetime(2026, 8, 10, tzinfo=UTC).timestamp(),
                permalink="/r/home/comments/post-1/example/comment-1/",
            )
        ][:limit]


class FailingRedditTransport(FakeRedditTransport):
    def read_posts(self, subreddit: str, time_window: str, limit: int) -> list[RedditItem]:
        raise RuntimeError("simulated provider failure")


def organization(session: Session, slug: str) -> Organization:
    entity = Organization(name=f"Reddit {slug}", slug=slug)
    session.add(entity)
    session.commit()
    return entity


def connector_payload(organization_id: str) -> dict[str, object]:
    return {
        "organization_id": organization_id,
        "name": "Reddit pain reader",
        "subreddit_scope": ["home"],
        "keyword_scope": ["fan", "cooling"],
        "time_window": "week",
    }


def test_reddit_ingestion_lifecycle_and_read_only_safety(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "ingestion")
    app.dependency_overrides[get_reddit_transport] = lambda: FakeRedditTransport()
    created = client.post("/api/v1/reddit-connectors", json=connector_payload(str(owner.id)))
    assert created.status_code == 201
    connector_id = created.json()["id"]
    assert created.json()["status"] == "inactive"
    assert (
        client.patch(
            f"/api/v1/reddit-connectors/{connector_id}",
            params={"organization_id": str(owner.id)},
            json={"status": "active"},
        ).status_code
        == 200
    )
    ingested = client.post(
        f"/api/v1/reddit-connectors/{connector_id}/ingest",
        json={
            "organization_id": str(owner.id),
            "limit_per_subreddit": 10,
            "include_comments": True,
            "comments_per_post": 5,
        },
    )
    assert ingested.status_code == 200
    assert ingested.json() | {"job_id": ingested.json()["job_id"]} == {
        "job_id": ingested.json()["job_id"],
        "status": "completed",
        "record_count": 2,
        "pain_candidate_count": 2,
    }
    records = list(db_session.scalars(select(MarketDataRecord)))
    assert {record.content_type for record in records} == {"post", "comment"}
    assert all(record.source_platform == "reddit" for record in records)
    assert db_session.scalar(select(func.count()).select_from(CustomerPainCandidate)) == 2
    assert db_session.scalar(select(func.count()).select_from(PainEvidence)) == 2
    job = db_session.scalar(select(MarketIngestionJob))
    assert job is not None and job.source_platform == "reddit" and job.status == "completed"
    repeated = client.post(
        f"/api/v1/reddit-connectors/{connector_id}/ingest",
        json={"organization_id": str(owner.id)},
    )
    assert repeated.status_code == 200
    assert repeated.json()["record_count"] == 0
    assert repeated.json()["pain_candidate_count"] == 0
    app.dependency_overrides[get_reddit_transport] = lambda: FailingRedditTransport()
    with pytest.raises(RuntimeError, match="simulated provider failure"):
        client.post(
            f"/api/v1/reddit-connectors/{connector_id}/ingest",
            json={"organization_id": str(owner.id)},
        )
    failed_job = db_session.scalar(
        select(MarketIngestionJob).order_by(MarketIngestionJob.created_at.desc())
    )
    assert failed_job is not None and failed_job.status == "failed"
    for forbidden in ("post", "reply", "message", "opportunities"):
        assert client.post(
            f"/api/v1/reddit-connectors/{connector_id}/{forbidden}", json={}
        ).status_code in {
            404,
            405,
            422,
        }


def test_reddit_tenant_ownership_evidence_and_confidence_bounds(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "owner")
    other = organization(db_session, "other")
    app.dependency_overrides[get_reddit_transport] = lambda: FakeRedditTransport()
    created = client.post("/api/v1/reddit-connectors", json=connector_payload(str(owner.id)))
    connector_id = created.json()["id"]
    client.patch(
        f"/api/v1/reddit-connectors/{connector_id}",
        params={"organization_id": str(owner.id)},
        json={"status": "active"},
    )
    client.post(
        f"/api/v1/reddit-connectors/{connector_id}/ingest",
        json={"organization_id": str(owner.id), "include_comments": False},
    )
    record = db_session.scalar(select(MarketDataRecord))
    assert record is not None
    assert (
        client.post(
            "/api/v1/pain-candidates",
            json={
                "organization_id": str(owner.id),
                "source_record_id": str(record.id),
                "pain_category": "problem",
                "customer_language": "Bounded confidence",
                "confidence_score": 1.01,
            },
        ).status_code
        == 422
    )
    service = RedditIntelligenceService(db_session)
    with pytest.raises(IntelligenceScopeError):
        service.create_pain(
            PainCandidateCreate(
                organization_id=other.id,
                source_record_id=record.id,
                pain_category="problem",
                customer_language="Cross tenant",
                confidence_score=0.5,
            )
        )
    for endpoint in ("reddit-connectors", "pain-candidates", "pain-evidence"):
        response = client.get(f"/api/v1/{endpoint}", params={"organization_id": str(other.id)})
        assert response.status_code == 200
        assert response.json() == []
