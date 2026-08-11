from datetime import UTC, datetime

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.connector_models import MarketDataRecord
from commerce_os.intelligence.connector_schemas import (
    ConnectorCreate,
    IngestionJobCreate,
    IngestionJobUpdate,
    MarketDataRecordCreate,
    NormalizedMarketItemCreate,
)
from commerce_os.intelligence.connector_services import MarketConnectorService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session


def organization(session: Session, slug: str) -> Organization:
    entity = Organization(name=f"Connector {slug}", slug=slug)
    session.add(entity)
    session.commit()
    return entity


def test_connector_lifecycle_ownership_and_tenant_isolation(db_session: Session) -> None:
    owner = organization(db_session, "owner")
    other = organization(db_session, "other")
    service = MarketConnectorService(db_session)
    connector = service.create_connector(
        ConnectorCreate(
            organization_id=owner.id,
            name="Reddit contract",
            platform="reddit",
            connector_type="reddit",
            configuration_schema={"type": "object", "required": ["subreddit"]},
        )
    )
    assert connector.status == "inactive"
    with pytest.raises(IntelligenceValidationError):
        service.store_record(
            MarketDataRecordCreate(
                organization_id=owner.id,
                source_id=connector.id,
                external_reference="reddit://supplied/1",
                content_type="post",
                raw_content="Caller-supplied content.",
                metadata={"language": "en"},
                captured_at=datetime.now(UTC),
            )
        )
    service.transition_connector(connector, "active")
    record = service.store_record(
        MarketDataRecordCreate(
            organization_id=owner.id,
            source_id=connector.id,
            external_reference="reddit://supplied/1",
            content_type="post",
            raw_content="Caller-supplied content.",
            metadata={"language": "en"},
            captured_at=datetime.now(UTC),
        )
    )
    assert record.metadata_json == {"language": "en"}
    with pytest.raises(IntelligenceScopeError):
        service.normalize(
            NormalizedMarketItemCreate(
                organization_id=other.id,
                source_record_id=record.id,
                category="home",
                topic="cooling",
                customer_language="Too hot indoors",
                signal_type="customer_need",
                confidence=0.8,
            )
        )


def test_ingestion_states_and_normalization_contracts(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "api")
    base = {"organization_id": str(owner.id)}
    connector = client.post(
        "/api/v1/connectors",
        json=base
        | {
            "name": "News import contract",
            "platform": "news",
            "connector_type": "news",
            "configuration_schema": {"type": "object"},
        },
    )
    assert connector.status_code == 201
    connector_id = connector.json()["id"]
    assert (
        client.patch(
            f"/api/v1/connectors/{connector_id}", params=base, json={"status": "active"}
        ).status_code
        == 200
    )
    record = client.post(
        "/api/v1/market-data-records",
        json=base
        | {
            "source_id": connector_id,
            "external_reference": "internal://fixture/news-1",
            "content_type": "article",
            "raw_content": "Supplied fixture only.",
            "metadata": {"region": "US"},
            "captured_at": "2026-08-10T12:00:00Z",
        },
    )
    assert record.status_code == 201
    assert record.json()["metadata"] == {"region": "US"}
    record_id = record.json()["id"]
    normalized = client.post(
        "/api/v1/normalized-market-items",
        json=base
        | {
            "source_record_id": record_id,
            "category": "home",
            "topic": "cooling",
            "customer_language": "Need relief from heat",
            "signal_type": "demand",
            "confidence": 0.75,
        },
    )
    assert normalized.status_code == 201
    assert (
        client.post(
            "/api/v1/normalized-market-items",
            json=base
            | {
                "source_record_id": record_id,
                "category": "home",
                "topic": "cooling",
                "customer_language": "Invalid confidence",
                "signal_type": "demand",
                "confidence": 1.01,
            },
        ).status_code
        == 422
    )
    job = client.post("/api/v1/ingestion-jobs", json=base | {"source_id": connector_id})
    assert job.status_code == 201
    job_id = job.json()["id"]
    running = client.patch(
        f"/api/v1/ingestion-jobs/{job_id}", params=base, json={"status": "running"}
    )
    assert running.status_code == 200
    completed = client.patch(
        f"/api/v1/ingestion-jobs/{job_id}",
        params=base,
        json={"status": "completed", "record_count": 1},
    )
    assert completed.status_code == 200
    assert completed.json()["record_count"] == 1
    assert (
        client.patch(
            f"/api/v1/ingestion-jobs/{job_id}", params=base, json={"status": "running"}
        ).status_code
        == 409
    )
    for endpoint in (
        "connectors",
        "market-data-records",
        "normalized-market-items",
        "ingestion-jobs",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
    assert db_session.scalar(select(MarketDataRecord)).organization_id == owner.id
    assert client.post("/api/v1/connectors/live-sync", json={}).status_code in {404, 405, 422}


def test_job_service_rejects_skipped_states(db_session: Session) -> None:
    owner = organization(db_session, "states")
    service = MarketConnectorService(db_session)
    connector = service.create_connector(
        ConnectorCreate(
            organization_id=owner.id,
            name="File contract",
            platform="file",
            connector_type="social",
            configuration_schema={},
        )
    )
    service.transition_connector(connector, "active")
    job = service.create_job(IngestionJobCreate(organization_id=owner.id, source_id=connector.id))
    with pytest.raises(IntelligenceValidationError):
        service.transition_job(job, IngestionJobUpdate(status="completed", record_count=0))
