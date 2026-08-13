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
from commerce_os.intelligence.connector_schemas import ConnectorCreate, MarketDataRecordCreate
from commerce_os.intelligence.connector_services import MarketConnectorService
from commerce_os.intelligence.errors import IntelligenceScopeError, IntelligenceValidationError
from commerce_os.intelligence.marketplace_models import MarketplaceReviewEvidence
from commerce_os.intelligence.marketplace_schemas import (
    CompetitiveObservationCreate,
    MarketplaceEvidenceLinkCreate,
    MarketplaceReviewCreate,
    NormalizedMarketplaceReviewCreate,
)
from commerce_os.intelligence.marketplace_services import MarketplaceVoiceService
from commerce_os.intelligence.voice_models import CustomerPainCluster
from commerce_os.shared.models import utc_now
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.main import app


def organization(session: Session, slug: str) -> Organization:
    entity = Organization(name=f"Marketplace {slug}", slug=f"marketplace-{slug}")
    session.add(entity)
    session.commit()
    return entity


def review_fixture(session: Session, owner: Organization, marketplace: str = "amazon"):
    connectors = MarketConnectorService(session)
    connector = connectors.create_connector(
        ConnectorCreate(
            organization_id=owner.id,
            name=f"{marketplace.title()} review evidence",
            platform=marketplace,
            connector_type=marketplace,  # type: ignore[arg-type]
            capability="read_marketplace_reviews",
            authentication_state="verified",
            credential_reference=f"secret://commerce-os/marketplace/{marketplace}",
            configuration_schema={"marketplace_type": marketplace, "source_identity": "catalog"},
            rate_limit_metadata={"requests_per_minute": 5},
        )
    )
    connectors.transition_connector(connector, "configured")
    connectors.transition_connector(connector, "ready")
    raw = connectors.store_record(
        MarketDataRecordCreate(
            organization_id=owner.id,
            source_id=connector.id,
            external_reference=f"fixture://{marketplace}/review-1",
            content_type="marketplace_review",
            raw_content="User-supplied review fixture",
            metadata={"language": "en"},
            captured_at=datetime.now(UTC),
        )
    )
    payload = MarketplaceReviewCreate(
        organization_id=owner.id,
        connector_id=connector.id,
        source_record_id=raw.id,
        marketplace=marketplace,  # type: ignore[arg-type]
        source_identity="review-1",
        product_reference="marketplace-product-42",
        rating=2,
        review_date=datetime.now(UTC),
        review_text_metadata={"length": 31, "language": "en"},
        verified_indicator=True,
    )
    return connector, payload


def test_marketplace_review_is_idempotent_immutable_and_audited(db_session: Session) -> None:
    owner = organization(db_session, "evidence")
    _, payload = review_fixture(db_session, owner)
    service = MarketplaceVoiceService(db_session)
    first = service.capture_review(payload)
    repeated = service.capture_review(payload)
    assert repeated.id == first.id
    assert len(first.evidence_hash) == 64
    first.rating = 5
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    assert "marketplace.review_evidence.captured" in set(
        db_session.scalars(select(AuditLog.action))
    )


def test_marketplace_duplicate_conflict_and_tenant_isolation(db_session: Session) -> None:
    owner = organization(db_session, "owner")
    other = organization(db_session, "other")
    _, payload = review_fixture(db_session, owner, "etsy")
    service = MarketplaceVoiceService(db_session)
    review = service.capture_review(payload)
    with pytest.raises(IntelligenceValidationError, match="different immutable"):
        service.capture_review(payload.model_copy(update={"rating": 4}))
    with pytest.raises(IntelligenceScopeError):
        service.normalize(
            NormalizedMarketplaceReviewCreate(
                organization_id=other.id,
                review_evidence_id=review.id,
                customer_language="Packaging arrived damaged",
                product_reference=review.product_reference,
                evidence_confidence=0.8,
            )
        )


def test_normalization_evidence_links_and_competitive_observation(db_session: Session) -> None:
    owner = organization(db_session, "linking")
    _, payload = review_fixture(db_session, owner)
    service = MarketplaceVoiceService(db_session)
    review = service.capture_review(payload)
    normalized = service.normalize(
        NormalizedMarketplaceReviewCreate(
            organization_id=owner.id,
            review_evidence_id=review.id,
            sentiment_metadata={"label": "negative", "method": "supplied"},
            topic_metadata={"topics": ["packaging"]},
            customer_language="Packaging arrived damaged",
            product_reference=review.product_reference,
            evidence_confidence=0.8,
        )
    )
    cluster = CustomerPainCluster(
        organization_id=owner.id,
        name="Packaging damage",
        category="quality",
        description="Existing customer pain cluster",
        severity_score=60,
        confidence_score=0.7,
        status="active",
        scoring_evidence={},
    )
    db_session.add(cluster)
    db_session.commit()
    link = service.link_evidence(
        MarketplaceEvidenceLinkCreate(
            organization_id=owner.id,
            review_evidence_id=review.id,
            target_type="pain_cluster",
            target_id=cluster.id,
            evidence_strength=0.75,
        )
    )
    observation = service.create_competitive_observation(
        CompetitiveObservationCreate(
            organization_id=owner.id,
            review_evidence_id=review.id,
            competitor_reference="competitor-product-9",
            product_observations={"packaging": "thin"},
            customer_preference_signals=["protective packaging"],
            recurring_complaints=["damage in transit"],
            observation_count=3,
            confidence=0.7,
        )
    )
    assert normalized.customer_language == "Packaging arrived damaged"
    assert link.target_id == cluster.id
    assert observation.observation_count == 3


def test_marketplace_api_authorization_and_no_automation(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "api")
    _, payload = review_fixture(db_session, owner)
    response = client.post(
        "/api/v1/marketplace-review-evidence", json=payload.model_dump(mode="json")
    )
    assert response.status_code == 201
    assert (
        client.get(
            "/api/v1/marketplace-review-evidence", params={"organization_id": owner.id}
        ).status_code
        == 200
    )
    app.state.auth_test_bypass = False
    try:
        assert (
            client.get(
                "/api/v1/marketplace-review-evidence", params={"organization_id": owner.id}
            ).status_code
            == 401
        )
    finally:
        app.state.auth_test_bypass = True
    assert client.post("/api/v1/marketplace-review-evidence/scrape", json={}).status_code in {
        404,
        405,
        422,
    }
    assert db_session.scalar(select(MarketplaceReviewEvidence)).organization_id == owner.id


def test_marketplace_write_requires_rbac_permission(
    client: TestClient, db_session: Session
) -> None:
    owner = organization(db_session, "rbac")
    _, payload = review_fixture(db_session, owner)
    user = AuthenticationService(db_session).create_user(
        organization_id=owner.id,
        email="marketplace-reader@example.com",
        display_name="Marketplace Reader",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=owner.id,
        name="marketplace-reader",
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
        response = client.post(
            "/api/v1/marketplace-review-evidence",
            headers={"Authorization": f"Bearer {token}"},
            json=payload.model_dump(mode="json"),
        )
        assert response.status_code == 403
    finally:
        app.state.auth_test_bypass = True
