from datetime import UTC, datetime

import pytest
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    AuditLog,
    Organization,
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from commerce_os.governance.sessions import SessionService
from commerce_os.intelligence.connector_models import MarketDataRecord, MarketIngestionJob
from commerce_os.intelligence.connector_schemas import (
    ConnectorCreate,
    IngestionJobCreate,
    IngestionJobUpdate,
    MarketDataRecordCreate,
    NormalizedMarketItemCreate,
)
from commerce_os.intelligence.connector_services import MarketConnectorService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.shared.models import utc_now
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.main import app


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
    assert connector.status == "draft"
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


def test_secure_connector_lifecycle_idempotency_immutability_and_audit(
    db_session: Session,
) -> None:
    owner = organization(db_session, "secure")
    service = MarketConnectorService(db_session)
    connector = service.create_connector(
        ConnectorCreate(
            organization_id=owner.id,
            name="Provider-neutral evidence",
            platform="generic",
            connector_type="news",
            capability="read_evidence",
            authentication_state="not_required",
            configuration_schema={"query_scope": ["commerce"]},
            rate_limit_metadata={"requests_per_minute": 10},
        )
    )
    service.transition_connector(connector, "configured")
    service.transition_connector(connector, "ready")
    captured = datetime.now(UTC)
    payload = MarketDataRecordCreate(
        organization_id=owner.id,
        source_id=connector.id,
        external_reference="fixture://evidence/1",
        content_type="article",
        raw_content="Immutable supplied evidence.",
        metadata={"language": "en"},
        captured_at=captured,
        idempotency_key="evidence-1",
    )
    first = service.store_record(payload)
    repeated = service.store_record(payload)
    assert first.id == repeated.id
    assert len(first.payload_hash) == 64
    first.raw_content = "Attempted overwrite"
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    job = service.create_job(IngestionJobCreate(organization_id=owner.id, source_id=connector.id))
    for status in ("configured", "ready", "running"):
        job = service.transition_job(job, IngestionJobUpdate(status=status))
    job = service.transition_job(
        job,
        IngestionJobUpdate(
            status="failed",
            record_count=1,
            errors=[{"code": "provider_unavailable", "retryable": True}],
        ),
    )
    assert job.started_at and job.completed_at and job.errors
    assert db_session.scalar(select(MarketIngestionJob).where(MarketIngestionJob.id == job.id))
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert {
        "connector.ready",
        "connector.raw_evidence.captured",
        "connector.ingestion.failed",
    } <= actions


def test_connector_rejects_secret_material_and_conflicting_idempotency(
    db_session: Session,
) -> None:
    owner = organization(db_session, "secrets")
    service = MarketConnectorService(db_session)
    with pytest.raises(IntelligenceValidationError, match="Secret material"):
        service.create_connector(
            ConnectorCreate(
                organization_id=owner.id,
                name="Unsafe",
                platform="generic",
                connector_type="social",
                configuration_schema={"api_key": "plaintext"},
            )
        )
    connector = service.create_connector(
        ConnectorCreate(
            organization_id=owner.id,
            name="Safe",
            platform="generic",
            connector_type="social",
            authentication_state="verified",
            credential_reference="secret://commerce-os/connectors/safe",
        )
    )
    service.transition_connector(connector, "configured")
    service.transition_connector(connector, "ready")
    common = {
        "organization_id": owner.id,
        "source_id": connector.id,
        "external_reference": "fixture://safe/1",
        "content_type": "post",
        "metadata": {},
        "captured_at": datetime.now(UTC),
        "idempotency_key": "stable-key",
    }
    service.store_record(MarketDataRecordCreate(**common, raw_content="first"))
    with pytest.raises(IntelligenceValidationError, match="different immutable evidence"):
        service.store_record(MarketDataRecordCreate(**common, raw_content="changed"))


def test_connector_api_write_permission_is_required(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "permission")
    user = AuthenticationService(db_session).create_user(
        organization_id=owner.id,
        email="connector-reader@example.com",
        display_name="Connector Reader",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=owner.id,
        name="connector-reader",
        description="Read only",
        grants_human_approval_authority=False,
        is_active=True,
    )
    permission = Permission(
        key="api.read",
        resource="api",
        action="read",
        description="Read API",
        is_human_approval_permission=False,
    )
    db_session.add_all([role, permission])
    db_session.flush()
    db_session.add_all(
        [
            UserRole(
                user_id=user.id,
                role_id=role.id,
                organization_id=owner.id,
                project_id=None,
                assigned_by=user.id,
                assigned_at=utc_now(),
            ),
            RolePermission(role_id=role.id, permission_id=permission.id),
        ]
    )
    db_session.commit()
    token, _ = SessionService(db_session).issue(user)
    app.state.auth_test_bypass = False
    try:
        headers = {"Authorization": f"Bearer {token}"}
        assert (
            client.get(
                "/api/v1/connectors",
                params={"organization_id": owner.id},
                headers=headers,
            ).status_code
            == 200
        )
        denied = client.post(
            "/api/v1/connectors",
            headers=headers,
            json={
                "organization_id": str(owner.id),
                "name": "Denied",
                "platform": "generic",
                "connector_type": "news",
            },
        )
        assert denied.status_code == 403
    finally:
        app.state.auth_test_bypass = True
